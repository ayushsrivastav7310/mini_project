import io
import os
from PIL import Image
from app.utils.validators import allowed_file
from app.services.ai_service import classifier
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department

def test_allowed_file_extensions():
    """Verify file extension validation rules."""
    allowed = {"png", "jpg", "jpeg", "webp"}
    assert allowed_file("scan.jpg", allowed) is True
    assert allowed_file("image.PNG", allowed) is True
    assert allowed_file("malicious.exe", allowed) is False
    assert allowed_file("script.py", allowed) is False
    assert allowed_file("no_ext", allowed) is False

def test_ai_classifier_demo_mode(tmp_path):
    """Test AI Classifier runs demo heuristic safely on synthetic image."""
    img_path = str(tmp_path / "test_swab.jpg")
    # Create yellowish image (mimicking soiled cotton)
    img = Image.new("RGB", (128, 128), color=(200, 180, 50))
    img.save(img_path)

    result = classifier.classify_image(img_path)

    assert "predicted_category" in result
    assert "confidence" in result
    assert "probabilities" in result
    assert result["confidence"] > 0
    assert result["demo_mode"] is True
    assert "Bio-Medical Waste" in result["disclaimer"]

def test_ai_scan_endpoint(auth_staff, sample_image_file):
    """Test AJAX /ai/scan endpoint with image file upload."""
    data = {
        "image": (sample_image_file, "waste_photo.jpg")
    }
    resp = auth_staff.post("/ai/scan", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data["success"] is True
    assert "predicted_category" in json_data
    assert "confidence" in json_data
    assert "container_type" in json_data
    assert "treatment_method" in json_data

def test_ai_scan_endpoint_invalid_type(auth_staff):
    """Test rejection of non-image file upload."""
    data = {
        "image": (io.BytesIO(b"malicious script contents"), "malicious.sh")
    }
    resp = auth_staff.post("/ai/scan", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    json_data = resp.get_json()
    assert json_data["success"] is False
    assert "Unsupported file format" in json_data["error"]

def test_ai_confirm_and_log(app, auth_staff):
    """Test committing verified AI prediction into ledger."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()

        resp = auth_staff.post("/ai/confirm-and-log", data={
            "department_id": dept.id,
            "assigned_category_id": cat.id,
            "item_description": "Scanned latex gloves",
            "quantity_kg": "1.85",
            "ai_suggested_category": cat.code,
            "ai_confidence": 0.88,
            "staff_notes": "Physical verification approved"
        })

        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data["success"] is True
        assert json_data["tracking_code"].startswith("BMW-")

        record = WasteRecord.query.get(json_data["record_id"])
        assert record is not None
        assert record.staff_verified is True
        assert record.quantity_kg == 1.85
