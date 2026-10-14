import json
from datetime import datetime, timedelta
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.services.stats_service import get_live_analytics
from app.services.report_service import generate_barcode_svg, generate_record_qr_base64
from app.services.ai_service import classifier
from app.extensions import db
from PIL import Image

def test_live_analytics_calculation(app):
    """Test live statutory compliance and statistical forecasting."""
    with app.app_context():
        stats = get_live_analytics()
        assert "compliance" in stats
        assert "score" in stats["compliance"]
        assert 0.0 <= stats["compliance"]["score"] <= 100.0
        assert "forecast" in stats
        assert "tomorrow_kg" in stats["forecast"]
        assert "anomalies" in stats
        assert isinstance(stats["anomalies"], list)

def test_api_dashboard_live_endpoint(auth_staff):
    """Test /api/dashboard/live endpoint returns complete real-time telemetry."""
    resp = auth_staff.get("/api/dashboard/live")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_kg" in data
    assert "compliance" in data
    assert "anomalies" in data
    assert "forecast" in data
    assert "category_stats" in data
    assert "sync_time" in data

def test_quick_status_lifecycle_transition(app, auth_staff):
    """Test 1-click status advancement endpoint."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()
        record = WasteRecord(
            tracking_code="BMW-QUICK-TEST-1",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=3.5,
            item_description="Quick status test bag",
            disposal_status=WasteRecord.STATUS_GENERATED
        )
        db.session.add(record)
        db.session.commit()
        r_id = record.id

    # Advance to STORED via quick status
    resp = auth_staff.post(f"/waste/{r_id}/quick-status", data={"status": "STORED"}, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        rec = db.session.get(WasteRecord, r_id)
        assert rec.disposal_status == WasteRecord.STATUS_STORED

def test_bulk_dispatch_operation(app, auth_staff):
    """Test batch-dispatching multiple bags with manifest."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()
        r1 = WasteRecord(
            tracking_code="BMW-BULK-01",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=2.0,
            item_description="Bulk item 1",
            disposal_status=WasteRecord.STATUS_STORED
        )
        r2 = WasteRecord(
            tracking_code="BMW-BULK-02",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=4.0,
            item_description="Bulk item 2",
            disposal_status=WasteRecord.STATUS_STORED
        )
        db.session.add_all([r1, r2])
        db.session.commit()
        ids = [r1.id, r2.id]

    resp = auth_staff.post("/waste/bulk-dispatch", data={
        "record_ids": ids,
        "manifest_no": "MNF-2026-TEST-99",
        "carrier": "BioExpress Transport"
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        for i in ids:
            rec = db.session.get(WasteRecord, i)
            assert rec.disposal_status == WasteRecord.STATUS_DISPATCHED
            assert rec.dispatch_manifest_no == "MNF-2026-TEST-99"
            assert rec.dispatch_carrier == "BioExpress Transport"

def test_barcode_and_qr_generators(app):
    """Test Code-128 SVG barcode and scannable QR manifest generation."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()
        record = WasteRecord(
            tracking_code="BMW-SCAN-TEST-42",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=1.75,
            item_description="Scan verification item",
            staff_verified=True
        )

        svg = generate_barcode_svg(record.tracking_code)
        assert "<svg" in svg
        assert "BMW-SCAN-TEST-42" in svg

        qr_b64 = generate_record_qr_base64(record)
        assert isinstance(qr_b64, str)
        assert len(qr_b64) > 100

def test_computer_vision_telemetry_extraction(tmp_path):
    """Test real multi-spectral feature telemetry extraction."""
    img_path = str(tmp_path / "cv_test_red.jpg")
    # Create red-tinted synthetic test image
    img = Image.new("RGB", (128, 128), color=(220, 30, 40))
    img.save(img_path)

    result = classifier.classify_image(img_path)
    assert "feature_telemetry" in result
    tel = result["feature_telemetry"]
    assert "dominant_hue_name" in tel
    assert "inferred_material" in tel
    assert "texture_complexity" in tel
    assert result["predicted_category"] in ["RED", "YELLOW", "UNKNOWN"]

