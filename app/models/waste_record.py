from datetime import datetime
import uuid
from app.extensions import db

class WasteRecord(db.Model):
    """Primary waste generation ledger item with audit tracking and verification metadata."""
    __tablename__ = "waste_records"

    # Disposal status lifecycle
    STATUS_GENERATED = "GENERATED"
    STATUS_STORED = "STORED"
    STATUS_DISPATCHED = "DISPATCHED"

    id = db.Column(db.Integer, primary_key=True)
    tracking_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("waste_categories.id"), nullable=False)
    logged_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    quantity_kg = db.Column(db.Float, nullable=False)
    item_description = db.Column(db.String(255), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # AI Assistance Metadata
    ai_suggested_category = db.Column(db.String(50), nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)
    staff_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Disposal & Manifest Tracking
    disposal_status = db.Column(db.String(20), default=STATUS_GENERATED, nullable=False)
    dispatch_manifest_no = db.Column(db.String(64), nullable=True)
    dispatch_carrier = db.Column(db.String(128), nullable=True)
    
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to feedback
    feedbacks = db.relationship("PredictionFeedback", backref="waste_record", lazy="dynamic", cascade="all, delete-orphan")

    @staticmethod
    def generate_tracking_code() -> str:
        """Generate a compliant hospital BMW barcode / tracking identifier."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:6].upper()
        return f"BMW-{date_str}-{short_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tracking_code": self.tracking_code,
            "department": self.department.name if self.department else None,
            "category": self.category.name if self.category else None,
            "category_code": self.category.code if self.category else None,
            "bin_color": self.category.bin_color_name if self.category else None,
            "quantity_kg": round(self.quantity_kg, 2),
            "item_description": self.item_description,
            "image_filename": self.image_filename,
            "ai_suggested_category": self.ai_suggested_category,
            "ai_confidence": round(self.ai_confidence * 100, 1) if self.ai_confidence else None,
            "staff_verified": self.staff_verified,
            "disposal_status": self.disposal_status,
            "logged_by": self.logger.full_name if self.logger else None,
            "verified_by": self.verifier.full_name if self.verifier else None,
            "remarks": self.remarks,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<WasteRecord {self.tracking_code}: {self.quantity_kg}kg [{self.disposal_status}]>"
