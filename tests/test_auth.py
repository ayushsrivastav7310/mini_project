from app.models.user import User
from app.extensions import db

def test_user_password_hashing(app):
    """Verify werkzeug secure password hashing and checking."""
    with app.app_context():
        user = User(username="hash_test", email="hash@test.org", full_name="Hash Test")
        user.set_password("MySecurePass#2026")
        
        assert user.password_hash != "MySecurePass#2026"
        assert user.check_password("MySecurePass#2026") is True
        assert user.check_password("WrongPassword") is False

def test_login_successful(client):
    """Verify authentication succeeds with valid credentials."""
    resp = client.post("/login", data={
        "username": "test_staff",
        "password": "Staff@123"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data
    assert b"Waste Operations Center" in resp.data

def test_login_invalid_password(client):
    """Verify login failure with incorrect credentials."""
    resp = client.post("/login", data={
        "username": "test_staff",
        "password": "IncorrectPassword"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid credentials" in resp.data

def test_login_deactivated_user(app, client):
    """Verify deactivated user accounts cannot access the portal."""
    with app.app_context():
        user = User.query.filter_by(username="test_staff").first()
        user.is_active = False
        db.session.commit()

    resp = client.post("/login", data={
        "username": "test_staff",
        "password": "Staff@123"
    }, follow_redirects=True)
    assert b"This account has been deactivated" in resp.data

def test_logout(auth_staff):
    """Verify session termination on logout."""
    resp = auth_staff.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"successfully logged out" in resp.data

def test_protected_routes_require_login(client):
    """Verify unauthenticated requests redirect to login."""
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

def test_admin_route_forbidden_for_staff(auth_staff):
    """Verify clinical staff cannot access admin restricted areas (403)."""
    resp = auth_staff.get("/admin/categories")
    assert resp.status_code == 403
    assert b"Access Authorization Restricted" in resp.data

def test_admin_route_accessible_by_admin(auth_admin):
    """Verify admin role has unrestricted access to admin routes."""
    resp = auth_admin.get("/admin/categories")
    assert resp.status_code == 200
    assert b"Biomedical Waste Category Configuration" in resp.data
