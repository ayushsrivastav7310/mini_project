from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from app.extensions import db
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department

def get_dashboard_summary() -> Dict[str, Any]:
    """Calculate key performance indicators and aggregate metrics for dashboards."""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    
    # Total generation metrics
    total_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0)).scalar()
    total_records = WasteRecord.query.count()
    
    # Today's metrics
    today_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter(WasteRecord.created_at >= today_start).scalar()
    today_records = WasteRecord.query.filter(WasteRecord.created_at >= today_start).count()
    
    # Verification & status metrics
    pending_verifications = WasteRecord.query.filter_by(staff_verified=False).count()
    dispatched_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter_by(disposal_status=WasteRecord.STATUS_DISPATCHED).scalar()
    stored_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
        .filter_by(disposal_status=WasteRecord.STATUS_STORED).scalar()
    
    # Category Breakdown
    categories = WasteCategory.query.filter_by(is_active=True).all()
    category_stats = []
    
    cat_totals = db.session.query(
        WasteRecord.category_id,
        func.sum(WasteRecord.quantity_kg).label("kg"),
        func.count(WasteRecord.id).label("count")
    ).group_by(WasteRecord.category_id).all()
    
    cat_map = {row.category_id: (row.kg or 0.0, row.count or 0) for row in cat_totals}
    
    for cat in categories:
        cat_kg, count = cat_map.get(cat.id, (0.0, 0))
        pct = round((cat_kg / total_kg * 100), 1) if total_kg > 0 else 0.0
        category_stats.append({
            "id": cat.id,
            "code": cat.code,
            "name": cat.name,
            "color_name": cat.bin_color_name,
            "color_hex": cat.bin_color_hex,
            "badge_class": cat.badge_class,
            "total_kg": round(cat_kg, 2),
            "percentage": pct,
            "count": count
        })
        
    # Department Breakdown
    dept_totals = db.session.query(
        Department.code,
        Department.name,
        func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0).label("kg"),
        func.count(WasteRecord.id).label("count")
    ).outerjoin(WasteRecord, Department.id == WasteRecord.department_id)\
     .group_by(Department.id).order_by(func.sum(WasteRecord.quantity_kg).desc()).all()
     
    department_stats = [
        {
            "code": row.code,
            "name": row.name,
            "total_kg": round(row.kg, 2),
            "count": row.count,
            "percentage": round((row.kg / total_kg * 100), 1) if total_kg > 0 else 0.0
        }
        for row in dept_totals
    ]
    
    # 7-day chronological generation trend
    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())
        
        day_kg = db.session.query(func.coalesce(func.sum(WasteRecord.quantity_kg), 0.0))\
            .filter(WasteRecord.created_at >= day_start, WasteRecord.created_at <= day_end).scalar()
            
        trend_labels.append(day_date.strftime("%b %d"))
        trend_data.append(round(day_kg, 2))

    return {
        "total_kg": round(total_kg, 2),
        "total_records": total_records,
        "today_kg": round(today_kg, 2),
        "today_records": today_records,
        "pending_verifications": pending_verifications,
        "dispatched_kg": round(dispatched_kg, 2),
        "stored_kg": round(stored_kg, 2),
        "category_stats": category_stats,
        "department_stats": department_stats,
        "trend_labels": trend_labels,
        "trend_data": trend_data
    }
