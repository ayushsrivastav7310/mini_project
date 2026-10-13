from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(UserMixin, db.Model):
    """User account model with Role-Based Access Control (Admin / Staff)."""
    __tablename__ = "users"

    ROLE_ADMIN = "ADMIN"
    ROLE_STAFF = "STAFF"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_STAFF)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    logged_records = db.relationship("WasteRecord", backref="logger", foreign_keys="WasteRecord.logged_by_id", lazy="dynamic")
    verified_records = db.relationship("WasteRecord", backref="verifier", foreign_keys="WasteRecord.verified_by_id", lazy="dynamic")
    feedbacks = db.relationship("PredictionFeedback", backref="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store password securely."""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        """Verify plain password against hashed password."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin_user(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role == self.ROLE_ADMIN

    @property
    def is_staff_user(self) -> bool:
        """Check if user has regular clinical staff privileges."""
        return self.role == self.ROLE_STAFF

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<User {self.username} [{self.role}]>"
