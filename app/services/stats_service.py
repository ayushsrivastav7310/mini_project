from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import math
from sqlalchemy import func
from app.extensions import db
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.models.feedback import PredictionFeedback

def get_dashboard_summary() -> Dict[str, Any]:
    """Calculate key performance indicators and aggregate metrics for dashboards."""
    return get_live_analytics()

def get_live_analytics(department_id: Optional[int] = None, time_range: str = "7d") -> Dict[str, Any]:
    """
    Perform live, mathematical analysis directly against operational waste records.
    Computes statutory compliance scores (BMW Rules 2016), detects real anomalies,
    forecasts future generation, and evaluates departmental segregation efficiency.
    """
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    
    # Base query with optional department filter
    base_query = WasteRecord.query
    if department_id:
        base_query = base_query.filter(WasteRecord.department_id == department_id)
        
    # Total generation metrics
    total_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))
    if department_id:
        total_kg = total_kg.filter(WasteRecord.department_id == department_id)
    total_kg = float(total_kg.scalar() or 0.0)
    
    total_records = base_query.count()
    
    # Today's metrics
    today_query = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter(WasteRecord.created_at >= today_start)
    if department_id:
        today_query = today_query.filter(WasteRecord.department_id == department_id)
    today_kg = float(today_query.scalar() or 0.0)
    
    today_records = base_query.filter(WasteRecord.created_at >= today_start).count()
    
    # Verification & status metrics
    pending_verifications = base_query.filter_by(staff_verified=False).count()
    verified_records = base_query.filter_by(staff_verified=True).count()
    
    dispatched_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter(WasteRecord.disposal_status == WasteRecord.STATUS_DISPATCHED)
    if department_id:
        dispatched_kg = dispatched_kg.filter(WasteRecord.department_id == department_id)
    dispatched_kg = float(dispatched_kg.scalar() or 0.0)
    
    stored_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter(WasteRecord.disposal_status == WasteRecord.STATUS_STORED)
    if department_id:
        stored_kg = stored_kg.filter(WasteRecord.department_id == department_id)
    stored_kg = float(stored_kg.scalar() or 0.0)
    
    generated_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter(WasteRecord.disposal_status == WasteRecord.STATUS_GENERATED)
    if department_id:
        generated_kg = generated_kg.filter(WasteRecord.department_id == department_id)
    generated_kg = float(generated_kg.scalar() or 0.0)

    # -------------------------------------------------------------
    # 1. STATUTORY BMW 2016 COMPLIANCE RATING (LIVE CALCULATION)
    # Under Indian BMW Rules (2016), key compliance factors include:
    # a) Staff physical inspection rate (mandatory verification)
    # b) 48-Hour Storage Rule: No untreated waste stored > 48h
    # c) Segregation precision (low override rate indicating staff adherence)
    # d) Quarantine clearance (unknown residue handled promptly)
    # -------------------------------------------------------------
    cutoff_48h = now - timedelta(hours=48)
    overdue_records = base_query.filter(
        WasteRecord.disposal_status.in_([WasteRecord.STATUS_GENERATED, WasteRecord.STATUS_STORED]),
        WasteRecord.created_at < cutoff_48h
    ).all()
    overdue_count = len(overdue_records)
    overdue_weight = sum(r.quantity_kg for r in overdue_records)
    
    # Verification component (weight: 40%)
    verification_rate = (verified_records / total_records * 100.0) if total_records > 0 else 100.0
    
    # 48-Hour Storage Rule component (weight: 35%)
    # Deduct 15 points per overdue record down to 0
    storage_compliance_score = max(0.0, 100.0 - (overdue_count * 20.0))
    
    # Segregation Precision component (weight: 25%)
    total_feedbacks = PredictionFeedback.query.count()
    if verified_records > 0:
        override_rate = min(100.0, (total_feedbacks / verified_records) * 100.0)
        segregation_precision = max(0.0, 100.0 - override_rate)
    else:
        segregation_precision = 100.0
        
    composite_compliance = round(
        (0.40 * verification_rate) +
        (0.35 * storage_compliance_score) +
        (0.25 * segregation_precision),
        1
    )
    
    if composite_compliance >= 92.0:
        compliance_grade = "A+ (Fully Compliant)"
        compliance_class = "text-success"
        compliance_badge = "bg-success"
    elif composite_compliance >= 80.0:
        compliance_grade = "A (Substantially Compliant)"
        compliance_class = "text-info"
        compliance_badge = "bg-info text-dark"
    elif composite_compliance >= 65.0:
        compliance_grade = "B (Minor Gaps Detected)"
        compliance_class = "text-warning"
        compliance_badge = "bg-warning text-dark"
    else:
        compliance_grade = "C (Critical Violations Pending)"
        compliance_class = "text-danger"
        compliance_badge = "bg-danger"

    # -------------------------------------------------------------
    # 2. LIVE ANOMALY DETECTION ENGINE
    # -------------------------------------------------------------
    anomalies = []
    
    # Anomaly A: 48-Hour Storage Rule Breach
    if overdue_count > 0:
        anomalies.append({
            "level": "CRITICAL",
            "type": "STORAGE_LIMIT_BREACH",
            "title": f"48-Hour Storage Limit Breach ({overdue_count} Bags)",
            "message": f"{round(overdue_weight, 2)} kg of untreated biomedical waste has exceeded the statutory 48-hour storage limit under BMW Rules (2016). Immediate dispatch or treatment required.",
            "action": "Dispatch Waste Immediately"
        })
        
    # Anomaly B: High Unverified Backlog
    if pending_verifications >= 5:
        anomalies.append({
            "level": "WARNING",
            "type": "VERIFICATION_BACKLOG",
            "title": f"Clinical Verification Backlog ({pending_verifications} Items)",
            "message": "Multiple waste entries are awaiting physical staff verification before final disposal commitment.",
            "action": "Review Unverified Records"
        })
        
    # Anomaly C: Unresolved Quarantine Residue
    quarantine_records = base_query.join(WasteCategory).filter(
        WasteCategory.code == "UNKNOWN",
        WasteRecord.disposal_status != WasteRecord.STATUS_DISPATCHED
    ).count()
    if quarantine_records > 0:
        anomalies.append({
            "level": "INFO",
            "type": "QUARANTINE_RESIDUE",
            "title": f"Quarantine Holding Active ({quarantine_records} Items)",
            "message": "Unidentified residue in holding requires physical inspection by the Infection Control Officer.",
            "action": "Open Quarantine Review"
        })

    # -------------------------------------------------------------
    # 3. 7-DAY TREND & REAL-TIME PREDICTIVE FORECASTING
    # -------------------------------------------------------------
    trend_labels = []
    trend_data = []
    daily_weights = []
    
    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())
        
        day_q = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
            .filter(WasteRecord.created_at >= day_start, WasteRecord.created_at <= day_end)
        if department_id:
            day_q = day_q.filter(WasteRecord.department_id == department_id)
            
        day_kg = float(day_q.scalar() or 0.0)
        trend_labels.append(day_date.strftime("%b %d"))
        trend_data.append(round(day_kg, 2))
        daily_weights.append(day_kg)
        
    # Moving Average & Next-Day Projection (kg)
    # Simple weighted moving average with recent days weighted higher
    weights_sum = sum(daily_weights)
    avg_7d = weights_sum / 7.0 if len(daily_weights) == 7 else 0.0
    
    # Linear projection for tomorrow:
    # y_forecast = avg + slope * delta
    if len(daily_weights) >= 3:
        recent_3d = daily_weights[-3:]
        forecast_tomorrow = round(max(0.0, (0.5 * recent_3d[2]) + (0.3 * recent_3d[1]) + (0.2 * recent_3d[0])), 2)
    else:
        forecast_tomorrow = round(avg_7d, 2)
        
    # Anomaly D: Statistical Surge Detection (Today > Mean + 2 * StdDev)
    if len(daily_weights) >= 4:
        mean_val = sum(daily_weights[:-1]) / (len(daily_weights) - 1)
        variance = sum((x - mean_val) ** 2 for x in daily_weights[:-1]) / (len(daily_weights) - 1)
        std_dev = math.sqrt(variance)
        if today_kg > (mean_val + (1.8 * std_dev)) and today_kg > 5.0:
            anomalies.append({
                "level": "WARNING",
                "type": "GENERATION_SPIKE",
                "title": "Abnormal Daily Generation Spike",
                "message": f"Today's waste generation ({today_kg:.2f} kg) is significantly higher than historical average ({mean_val:.2f} kg ± {std_dev:.2f} kg). Verify if surgical campaigns or emergencies occurred.",
                "action": "Investigate Ward Outflows"
            })

    # -------------------------------------------------------------
    # 4. CATEGORY BREAKDOWN
    # -------------------------------------------------------------
    categories = WasteCategory.query.filter_by(is_active=True).all()
    category_stats = []
    
    cat_totals_query = db.session.query(
        WasteRecord.category_id,
        func.sum(WasteRecord.quantity_kg).label("kg"),
        func.count(WasteRecord.id).label("count")
    )
    if department_id:
        cat_totals_query = cat_totals_query.filter(WasteRecord.department_id == department_id)
    cat_totals = cat_totals_query.group_by(WasteRecord.category_id).all()
    
    cat_map = {row.category_id: (float(row.kg or 0.0), row.count or 0) for row in cat_totals}
    
    for cat in categories:
        cat_kg, count = cat_map.get(cat.id, (0.0, 0))
        pct = round((cat_kg / total_kg * 100.0), 1) if total_kg > 0 else 0.0
        category_stats.append({
            "id": cat.id,
            "code": cat.code,
            "name": cat.name,
            "color_name": cat.bin_color_name,
            "color_hex": cat.bin_color_hex,
            "badge_class": cat.badge_class,
            "container_type": cat.container_type,
            "treatment_method": cat.treatment_method,
            "total_kg": round(cat_kg, 2),
            "percentage": pct,
            "count": count
        })
        
    # -------------------------------------------------------------
    # 5. DEPARTMENT SEGREGATION EFFICIENCY INDEX
    # -------------------------------------------------------------
    dept_totals = db.session.query(
        Department.id,
        Department.code,
        Department.name,
        func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0).label("kg"),
        func.count(WasteRecord.id).label("count")
    ).outerjoin(WasteRecord, Department.id == WasteRecord.department_id)\
     .group_by(Department.id).order_by(func.sum(WasteRecord.quantity_kg).desc()).all()
     
    department_stats = []
    for row in dept_totals:
        dept_total = float(row.kg or 0.0)
        pct = round((dept_total / total_kg * 100.0), 1) if total_kg > 0 else 0.0
        
        # Calculate departmental verification rate
        dept_verif_count = WasteRecord.query.filter_by(
            department_id=row.id, staff_verified=True
        ).count()
        dept_verif_rate = round((dept_verif_count / row.count * 100.0), 1) if row.count > 0 else 100.0
        
        department_stats.append({
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "total_kg": round(dept_total, 2),
            "count": row.count,
            "percentage": pct,
            "verification_rate": dept_verif_rate,
            "efficiency_status": "Optimal" if dept_verif_rate >= 90 else ("Attention" if dept_verif_rate >= 70 else "At Risk")
        })

    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sync_time": now.strftime("%H:%M:%S"),
        "department_id": department_id,
        
        # Key Totals
        "total_kg": round(total_kg, 2),
        "total_records": total_records,
        "today_kg": round(today_kg, 2),
        "today_records": today_records,
        "pending_verifications": pending_verifications,
        "verified_records": verified_records,
        "dispatched_kg": round(dispatched_kg, 2),
        "stored_kg": round(stored_kg, 2),
        "generated_kg": round(generated_kg, 2),
        
        # Compliance & Risk Analysis
        "compliance": {
            "score": composite_compliance,
            "grade": compliance_grade,
            "class": compliance_class,
            "badge": compliance_badge,
            "verification_rate": round(verification_rate, 1),
            "storage_score": round(storage_compliance_score, 1),
            "segregation_precision": round(segregation_precision, 1),
            "overdue_48h_count": overdue_count,
            "overdue_48h_kg": round(overdue_weight, 2)
        },
        
        # Live Anomalies & Alert Notifications
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        
        # Predictive Forecasting
        "forecast": {
            "tomorrow_kg": forecast_tomorrow,
            "avg_7d_kg": round(avg_7d, 2),
            "trend_direction": "UP" if forecast_tomorrow > avg_7d else ("DOWN" if forecast_tomorrow < avg_7d else "STABLE")
        },
        
        # Breakdowns
        "category_stats": category_stats,
        "department_stats": department_stats,
        "trend_labels": trend_labels,
        "trend_data": trend_data
    }
