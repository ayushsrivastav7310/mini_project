from datetime import datetime
from app.extensions import db

class Department(db.Model):
    """Hospital department entity generating biomedical waste."""
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    floor_location = db.Column(db.String(50), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    records = db.relationship("WasteRecord", backref="department", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "floor_location": self.floor_location,
            "contact_person": self.contact_person,
            "is_active": self.is_active
        }

    def __repr__(self) -> str:
        return f"<Department {self.code}: {self.name}>"
