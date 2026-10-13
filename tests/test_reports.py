from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.services.report_service import generate_csv_report
from app.extensions import db

def test_csv_report_generation(app):
    """Verify CSV string generation structure and compliance disclaimer."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()

        rec = WasteRecord(
            tracking_code="BMW-CSV-001",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=4.5,
            item_description="CSV Test Item",
            staff_verified=True
        )
        db.session.add(rec)
        db.session.commit()

        csv_text = generate_csv_report([rec])

        assert "BIOMEDICAL WASTE GENERATION & DISPOSAL AUDIT REPORT" in csv_text
        assert "BMW-CSV-001" in csv_text
        assert "4.50" in csv_text
        assert "Total Waste Generated (kg)" in csv_text
        assert "EDUCATIONAL PROTOTYPE NOTICE" in csv_text

def test_csv_export_route(auth_staff):
    """Test HTTP endpoint for downloading CSV audit ledger."""
    resp = auth_staff.get("/reports/export/csv")
    assert resp.status_code == 200
    assert resp.content_type == "text/csv; charset=utf-8"
    assert "attachment; filename=bmw_audit_" in resp.headers["Content-Disposition"]

def test_pdf_export_route(auth_staff):
    """Test HTTP endpoint for generating official PDF report."""
    resp = auth_staff.get("/reports/export/pdf")
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"
    assert "attachment; filename=bmw_compliance_certificate_" in resp.headers["Content-Disposition"]

def test_reports_preview_view(auth_staff):
    """Test rendering the reports filter and preview page."""
    resp = auth_staff.get("/reports")
    assert resp.status_code == 200
    assert b"Biomedical Waste Compliance Reports" in resp.data
    assert b"Download Audit CSV" in resp.data
    assert b"Download Official PDF Report" in resp.data
