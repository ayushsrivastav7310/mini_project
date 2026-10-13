from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.models.feedback import PredictionFeedback

def test_prediction_feedback_created_on_override(app, auth_staff):
    """Verify that overriding an AI prediction generates a feedback record for retraining."""
    with app.app_context():
        dept = Department.query.filter_by(code="ICU").first()
        cat_yellow = WasteCategory.query.filter_by(code="YELLOW").first()

        # Staff receives suggestion 'RED', but overrides to 'YELLOW'
        resp = auth_staff.post("/ai/confirm-and-log", data={
            "department_id": dept.id,
            "assigned_category_id": cat_yellow.id,
            "item_description": "Overridden swab package",
            "quantity_kg": "2.20",
            "ai_suggested_category": "RED",
            "ai_confidence": 0.65,
            "staff_notes": "Visually yellow soiled cotton, not red plastic"
        })

        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data["category_overridden"] is True

        fb = PredictionFeedback.query.filter_by(waste_record_id=json_data["record_id"]).first()
        assert fb is not None
        assert fb.predicted_category == "RED"
        assert fb.actual_category == "YELLOW"
        assert "Visually yellow soiled cotton" in fb.correction_reason

def test_admin_feedback_view(app, auth_admin, auth_staff):
    """Verify admin view of prediction corrections ledger."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()

        # Generate a feedback entry
        auth_staff.post("/ai/confirm-and-log", data={
            "department_id": dept.id,
            "assigned_category_id": cat.id,
            "item_description": "Test feedback item",
            "quantity_kg": "1.0",
            "ai_suggested_category": "UNKNOWN",
            "ai_confidence": 0.40,
            "staff_notes": "Identified by infection control"
        })

        resp = auth_admin.get("/admin/feedback")
        assert resp.status_code == 200
        assert b"AI Prediction Correction & Feedback Ledger" in resp.data
        assert b"UNKNOWN" in resp.data
