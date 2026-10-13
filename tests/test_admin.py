from app.models.category import WasteCategory
from app.models.department import Department
from app.models.user import User

def test_admin_category_management(app, auth_admin):
    """Test creating, editing, and toggling categories as administrator."""
    with app.app_context():
        # Create category
        resp = auth_admin.post("/admin/categories", data={
            "code": "CYTO",
            "name": "Cytotoxic & Chemotherapy Waste",
            "bin_color_name": "Yellow-Black",
            "bin_color_hex": "#ffb703",
            "container_type": "Hazard-labeled rigid container",
            "treatment_method": "High temperature incineration > 1200 C",
            "permitted_items": "Chemo vials, contaminated gloves",
            "prohibited_items": "Sharps"
        }, follow_redirects=True)

        assert resp.status_code == 200
        cat = WasteCategory.query.filter_by(code="CYTO").first()
        assert cat is not None
        assert cat.name == "Cytotoxic & Chemotherapy Waste"

        # Toggle status
        toggle_resp = auth_admin.post(f"/admin/categories/{cat.id}/toggle", follow_redirects=True)
        assert toggle_resp.status_code == 200
        cat_updated = WasteCategory.query.filter_by(code="CYTO").first()
        assert cat_updated.is_active is False

def test_admin_department_management(app, auth_admin):
    """Test registering a new hospital clinical ward."""
    with app.app_context():
        resp = auth_admin.post("/admin/departments", data={
            "code": "NICU",
            "name": "Neonatal Intensive Care Unit",
            "floor_location": "Level 3 - West Wing",
            "contact_person": "Dr. R. Sen"
        }, follow_redirects=True)

        assert resp.status_code == 200
        dept = Department.query.filter_by(code="NICU").first()
        assert dept is not None
        assert dept.name == "Neonatal Intensive Care Unit"

def test_admin_user_status_toggle(app, auth_admin):
    """Test activating and deactivating user credentials."""
    with app.app_context():
        staff = User.query.filter_by(username="test_staff").first()
        assert staff.is_active is True

        resp = auth_admin.post(f"/admin/users/{staff.id}/toggle-status", follow_redirects=True)
        assert resp.status_code == 200

        staff_updated = User.query.filter_by(username="test_staff").first()
        assert staff_updated.is_active is False
