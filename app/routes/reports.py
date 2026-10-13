from datetime import datetime
from flask import Blueprint, render_template, request, Response, make_response, current_app
from flask_login import login_required
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.services.report_service import generate_csv_report, generate_pdf_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

def _filter_records_from_request(req):
    """Helper to apply query filters for both preview and export."""
    query = WasteRecord.query

    category_id = req.args.get("category_id", type=int)
    if category_id:
        query = query.filter(WasteRecord.category_id == category_id)

    department_id = req.args.get("department_id", type=int)
    if department_id:
        query = query.filter(WasteRecord.department_id == department_id)

    status = req.args.get("status", "").strip()
    if status and status in [WasteRecord.STATUS_GENERATED, WasteRecord.STATUS_STORED, WasteRecord.STATUS_DISPATCHED]:
        query = query.filter(WasteRecord.disposal_status == status)

    date_from = req.args.get("date_from", "").strip()
    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(WasteRecord.created_at >= d_from)
        except ValueError:
            pass

    date_to = req.args.get("date_to", "").strip()
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(WasteRecord.created_at <= d_to)
        except ValueError:
            pass

    return query.order_by(WasteRecord.created_at.desc()).all()


@reports_bp.route("")
@login_required
def index():
    """Reports center with date-range filters, totals preview, and download links."""
    records = _filter_records_from_request(request)
    total_kg = sum(r.quantity_kg for r in records)
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        "reports/index.html",
        records=records,
        total_kg=round(total_kg, 2),
        categories=categories,
        departments=departments,
        current_category=request.args.get("category_id", type=int),
        current_department=request.args.get("department_id", type=int),
        current_status=request.args.get("status", ""),
        current_date_from=request.args.get("date_from", ""),
        current_date_to=request.args.get("date_to", "")
    )


@reports_bp.route("/export/csv")
@login_required
def export_csv():
    """Export filtered waste records to downloadable CSV."""
    records = _filter_records_from_request(request)
    csv_data = generate_csv_report(
        records,
        start_date=request.args.get("date_from", ""),
        end_date=request.args.get("date_to", "")
    )
    filename = f"bmw_audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route("/export/pdf")
@login_required
def export_pdf():
    """Export filtered waste records to formatted institutional PDF."""
    records = _filter_records_from_request(request)
    pdf_bytes = generate_pdf_report(
        records,
        start_date=request.args.get("date_from", ""),
        end_date=request.args.get("date_to", "")
    )
    filename = f"bmw_compliance_certificate_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
