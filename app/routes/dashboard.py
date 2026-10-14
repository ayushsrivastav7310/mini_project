from flask import Blueprint, render_template, jsonify, redirect, url_for, request
from flask_login import login_required, current_user
from app.services.stats_service import get_dashboard_summary, get_live_analytics
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index_redirect():
    """Default landing route redirect."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))

@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Main executive hospital waste monitoring dashboard with live analytics."""
    dept_id = request.args.get("department_id", type=int)
    stats = get_live_analytics(department_id=dept_id)
    
    query = WasteRecord.query
    if dept_id:
        query = query.filter(WasteRecord.department_id == dept_id)
    recent_records = query.order_by(WasteRecord.created_at.desc()).limit(8).all()
    
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_records=recent_records,
        categories=categories,
        departments=departments,
        selected_department_id=dept_id
    )

@dashboard_bp.route("/api/dashboard/stats")
@dashboard_bp.route("/api/dashboard/live")
@login_required
def api_live_stats():
    """Real-time REST endpoint providing live metrics, compliance score, and anomalies."""
    dept_id = request.args.get("department_id", type=int)
    time_range = request.args.get("range", "7d")
    stats = get_live_analytics(department_id=dept_id, time_range=time_range)
    return jsonify(stats)
