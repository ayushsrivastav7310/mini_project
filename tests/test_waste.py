from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.extensions import db

def test_create_waste_record_valid(app, auth_staff):
    """Test valid waste creation by authenticated staff."""
    with app.app_context():
        dept = Department.query.filter_by(code="ICU").first()
        cat = WasteCategory.query.filter_by(code="YELLOW").first()

        resp = auth_staff.post("/waste/create", data={
            "department_id": dept.id,
            "category_id": cat.id,
            "item_description": "Soiled cotton and dressings",
            "quantity_kg": "2.75",
            "remarks": "Autoclaved packaging",
            "staff_verified": "1"
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert b"logged successfully" in resp.data

        record = WasteRecord.query.filter_by(item_description="Soiled cotton and dressings").first()
        assert record is not None
        assert record.quantity_kg == 2.75
        assert record.staff_verified is True
        assert record.tracking_code.startswith("BMW-")

def test_create_waste_record_invalid_quantity(app, auth_staff):
    """Test rejection of non-positive or malformed weight."""
    with app.app_context():
        dept = Department.query.filter_by(code="ICU").first()
        cat = WasteCategory.query.filter_by(code="YELLOW").first()

        resp = auth_staff.post("/waste/create", data={
            "department_id": dept.id,
            "category_id": cat.id,
            "item_description": "Test item",
            "quantity_kg": "-5.00"
        }, follow_redirects=True)

        assert b"Waste quantity must be greater than 0 kg" in resp.data

def test_waste_ledger_list_and_filter(app, auth_staff):
    """Test filterable search on waste ledger."""
    with app.app_context():
        dept = Department.query.filter_by(code="ICU").first()
        cat_yellow = WasteCategory.query.filter_by(code="YELLOW").first()
        cat_red = WasteCategory.query.filter_by(code="RED").first()

        r1 = WasteRecord(
            tracking_code="BMW-TEST-001",
            department_id=dept.id,
            category_id=cat_yellow.id,
            logged_by_id=1,
            quantity_kg=3.0,
            item_description="Yellow anatomical tissue",
            staff_verified=True
        )
        r2 = WasteRecord(
            tracking_code="BMW-TEST-002",
            department_id=dept.id,
            category_id=cat_red.id,
            logged_by_id=1,
            quantity_kg=5.0,
            item_description="Red plastic catheters",
            staff_verified=False
        )
        db.session.add_all([r1, r2])
        db.session.commit()

        # Query all
        resp = auth_staff.get("/waste")
        assert b"BMW-TEST-001" in resp.data
        assert b"BMW-TEST-002" in resp.data

        # Filter by category
        resp_cat = auth_staff.get(f"/waste?category_id={cat_yellow.id}")
        assert b"BMW-TEST-001" in resp_cat.data
        assert b"BMW-TEST-002" not in resp_cat.data

def test_update_disposal_status(app, auth_staff):
    """Test lifecycle status transition (e.g. to DISPATCHED)."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()
        record = WasteRecord(
            tracking_code="BMW-STATUS-01",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=2.0,
            item_description="Status testing item",
            disposal_status=WasteRecord.STATUS_GENERATED
        )
        db.session.add(record)
        db.session.commit()
        r_id = record.id

        resp = auth_staff.post(f"/waste/{r_id}/status", data={
            "disposal_status": "DISPATCHED",
            "dispatch_manifest_no": "MNF-9988",
            "dispatch_carrier": "BioClean Carrier"
        }, follow_redirects=True)

        assert resp.status_code == 200
        updated = WasteRecord.query.get(r_id)
        assert updated.disposal_status == WasteRecord.STATUS_DISPATCHED
        assert updated.dispatch_manifest_no == "MNF-9988"

def test_delete_waste_record(app, client):
    """Test admin deletion and staff denial."""
    with app.app_context():
        dept = Department.query.first()
        cat = WasteCategory.query.first()
        record = WasteRecord(
            tracking_code="BMW-DEL-01",
            department_id=dept.id,
            category_id=cat.id,
            logged_by_id=1,
            quantity_kg=1.0,
            item_description="To be deleted"
        )
        db.session.add(record)
        db.session.commit()
        r_id = record.id

        # Login as staff: attempt should be forbidden (403)
        client.post("/login", data={"username": "test_staff", "password": "Staff@123"}, follow_redirects=True)
        resp_staff = client.post(f"/waste/{r_id}/delete")
        assert resp_staff.status_code == 403

        # Logout staff, then login as admin: attempt should succeed
        client.get("/logout", follow_redirects=True)
        client.post("/login", data={"username": "test_admin", "password": "Admin@123"}, follow_redirects=True)
        resp_admin = client.post(f"/waste/{r_id}/delete", follow_redirects=True)
        assert resp_admin.status_code == 200
        assert WasteRecord.query.get(r_id) is None
