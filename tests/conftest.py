import os
import sys
import io
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.category import WasteCategory
from app.models.waste_record import WasteRecord
from app.models.feedback import PredictionFeedback

@pytest.fixture
def app():
    """Create and configure a clean testing application instance."""
    app_instance = create_app("testing")
    
    with app_instance.app_context():
        db.create_all()
        
        # Create standard test roles
        admin = User(username="test_admin", email="admin@test.org", full_name="Admin Test", role=User.ROLE_ADMIN)
        admin.set_password("Admin@123")
        db.session.add(admin)

        staff = User(username="test_staff", email="staff@test.org", full_name="Staff Test", role=User.ROLE_STAFF)
        staff.set_password("Staff@123")
        db.session.add(staff)

        # Create test departments
        dept_icu = Department(code="ICU", name="Intensive Care Unit", floor_location="Level 3")
        dept_ot = Department(code="OT", name="Operation Theatre", floor_location="Level 2")
        db.session.add_all([dept_icu, dept_ot])

        # Create test categories
        cat_yellow = WasteCategory(
            code="YELLOW",
            name="Infectious Anatomical Waste",
            bin_color_name="Yellow",
            bin_color_hex="#ffc107",
            container_type="Yellow plastic bag",
            treatment_method="Incineration",
            permitted_items="Tissues, soiled cotton",
            prohibited_items="Sharps, plastics"
        )
        cat_red = WasteCategory(
            code="RED",
            name="Contaminated Recyclable Plastics",
            bin_color_name="Red",
            bin_color_hex="#dc3545",
            container_type="Red plastic bag",
            treatment_method="Autoclaving & recycling",
            permitted_items="Gloves, IV tubing",
            prohibited_items="Sharps, anatomical"
        )
        cat_unknown = WasteCategory(
            code="UNKNOWN",
            name="Needs Manual Review",
            bin_color_name="Grey",
            bin_color_hex="#6c757d",
            container_type="Quarantine bin",
            treatment_method="Manual inspection",
            permitted_items="Unidentified items",
            prohibited_items="None"
        )
        db.session.add_all([cat_yellow, cat_red, cat_unknown])

        db.session.commit()

        yield app_instance

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for CLI commands."""
    return app.test_cli_runner()

def login_client(client, username="test_staff", password="Staff@123"):
    """Helper to authenticate a test client session."""
    return client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

@pytest.fixture
def auth_staff(client):
    """Client authenticated as staff."""
    login_client(client, username="test_staff", password="Staff@123")
    return client

@pytest.fixture
def auth_admin(client):
    """Client authenticated as admin."""
    login_client(client, username="test_admin", password="Admin@123")
    return client

@pytest.fixture
def sample_image_file():
    """Generates a small in-memory test JPEG image."""
    img = Image.new("RGB", (100, 100), color=(220, 30, 30))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer
