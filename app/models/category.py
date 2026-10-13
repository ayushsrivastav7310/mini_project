from datetime import datetime
from app.extensions import db

class WasteCategory(db.Model):
    """Configurable Biomedical Waste Category aligned with Indian BMW Rules (2016)."""
    __tablename__ = "waste_categories"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    bin_color_name = db.Column(db.String(30), nullable=False)
    bin_color_hex = db.Column(db.String(10), nullable=False, default="#ffc107")
    badge_class = db.Column(db.String(50), nullable=False, default="bg-warning text-dark")
    container_type = db.Column(db.String(150), nullable=False)
    treatment_method = db.Column(db.Text, nullable=False)
    permitted_items = db.Column(db.Text, nullable=False)
    prohibited_items = db.Column(db.Text, nullable=False)
    storage_instructions = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    records = db.relationship("WasteRecord", backref="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "bin_color_name": self.bin_color_name,
            "bin_color_hex": self.bin_color_hex,
            "badge_class": self.badge_class,
            "container_type": self.container_type,
            "treatment_method": self.treatment_method,
            "permitted_items": self.permitted_items,
            "prohibited_items": self.prohibited_items,
            "storage_instructions": self.storage_instructions,
            "is_active": self.is_active
        }

    def __repr__(self) -> str:
        return f"<WasteCategory {self.code}: {self.name}>"
