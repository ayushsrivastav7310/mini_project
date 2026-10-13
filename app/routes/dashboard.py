from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.services.stats_service import get_dashboard_summary
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
    """Main executive hospital waste monitoring dashboard."""
    stats = get_dashboard_summary()
    recent_records = WasteRecord.query.order_by(WasteRecord.created_at.desc()).limit(8).all()
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_records=recent_records,
        categories=categories,
        departments=departments
    )

@dashboard_bp.route("/api/dashboard/stats")
@login_required
def api_stats():
    """REST endpoint providing aggregated metrics for Chart.js visualizer."""
    stats = get_dashboard_summary()
    return jsonify(stats)
