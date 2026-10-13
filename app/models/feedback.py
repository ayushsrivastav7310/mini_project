from datetime import datetime
from app.extensions import db

class PredictionFeedback(db.Model):
    """Logs prediction corrections when staff overrides AI category recommendation."""
    __tablename__ = "prediction_feedback"

    id = db.Column(db.Integer, primary_key=True)
    waste_record_id = db.Column(db.Integer, db.ForeignKey("waste_records.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    image_filename = db.Column(db.String(255), nullable=True)
    predicted_category = db.Column(db.String(50), nullable=False)
    predicted_confidence = db.Column(db.Float, nullable=False)
    actual_category = db.Column(db.String(50), nullable=False)
    correction_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "waste_record_id": self.waste_record_id,
            "user": self.user.full_name if self.user else None,
            "image_filename": self.image_filename,
            "predicted_category": self.predicted_category,
            "predicted_confidence": round(self.predicted_confidence * 100, 1),
            "actual_category": self.actual_category,
            "correction_reason": self.correction_reason,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<PredictionFeedback {self.predicted_category} -> {self.actual_category}>"
