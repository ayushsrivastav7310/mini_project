import os
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.ai_service import classifier
from app.models.category import WasteCategory
from app.models.department import Department
from app.models.waste_record import WasteRecord
from app.models.feedback import PredictionFeedback
from app.utils.validators import sanitize_and_save_image, validate_quantity
from app.extensions import db

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

@ai_bp.route("/classify")
@login_required
def classify_view():
    """Interactive Smart Waste Segregation Scanner UI."""
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()
    
    if os.environ.get("GEMINI_API_KEY"):
        active_engine = "Google Gemini 2.5 Multimodal Vision"
    elif classifier.is_tf_available and classifier.tf_model is not None:
        active_engine = "MobileNetV2 Deep Neural Network"
    else:
        active_engine = "Quantitative Computer Vision Feature Analyzer"
        
    return render_template(
        "ai/classify.html",
        categories=categories,
        departments=departments,
        active_engine=active_engine,
        demo_mode=False
    )


@ai_bp.route("/scan", methods=["POST"])
@login_required
def scan_image():
    """
    AJAX endpoint for image classification.
    Validates file format, performs live quantitative visual analysis, and returns BMW category & guidance.
    """
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image payload found in request."}), 400

    file_obj = request.files["image"]
    if file_obj.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    try:
        saved_name = sanitize_and_save_image(
            file_obj,
            current_app.config["UPLOAD_FOLDER"],
            current_app.config["ALLOWED_EXTENSIONS"]
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)

    try:
        result = classifier.classify_image(image_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Inference engine failure: {str(e)}"}), 500

    # Match database category if active
    category_code = result["predicted_category"]
    db_cat = WasteCategory.query.filter_by(code=category_code).first()

    payload = {
        "success": True,
        "image_filename": saved_name,
        "image_url": url_for("static", filename=f"uploads/{saved_name}") if "static" in str(current_app.config["UPLOAD_FOLDER"]) else f"/uploads/{saved_name}",
        "predicted_category": category_code,
        "category_id": db_cat.id if db_cat else None,
        "category_name": db_cat.name if db_cat else result["category_name"],
        "bin_color": db_cat.bin_color_name if db_cat else result["bin_color"],
        "bin_color_hex": db_cat.bin_color_hex if db_cat else result["bin_color_hex"],
        "badge_class": db_cat.badge_class if db_cat else result["badge_class"],
        "container_type": db_cat.container_type if db_cat else result["container_type"],
        "treatment_method": db_cat.treatment_method if db_cat else result["treatment_method"],
        "permitted_items": db_cat.permitted_items if db_cat else result["permitted_items"],
        "confidence": result["confidence"],
        "confidence_percent": result["confidence_percent"],
        "confidence_tier": result["confidence_tier"],
        "needs_review": result["needs_review"],
        "demo_mode": False,
        "probabilities": result["probabilities"],
        "feature_telemetry": result.get("feature_telemetry", {}),
        "engine_name": result.get("engine_name", "Computer Vision Engine"),
        "disclaimer": result["disclaimer"]
    }

    return jsonify(payload)


@ai_bp.route("/confirm-and-log", methods=["POST"])
@login_required
def confirm_and_log():
    """
    Staff human-in-the-loop verification route:
    Commits verified/corrected record to the ledger and records feedback if category was overridden.
    """
    department_id = request.form.get("department_id", type=int)
    assigned_category_id = request.form.get("assigned_category_id", type=int)
    item_description = request.form.get("item_description", "").strip()
    quantity_str = request.form.get("quantity_kg", "").strip()
    image_filename = request.form.get("image_filename", "").strip()
    ai_suggested_category = request.form.get("ai_suggested_category", "").strip()
    ai_confidence = request.form.get("ai_confidence", type=float)
    staff_notes = request.form.get("staff_notes", "").strip()

    dept = db.session.get(Department, department_id) if hasattr(db.session, "get") else Department.query.get(department_id)
    cat = db.session.get(WasteCategory, assigned_category_id) if hasattr(db.session, "get") else WasteCategory.query.get(assigned_category_id)

    if not dept or not cat:
        return jsonify({"success": False, "error": "Invalid department or category selected."}), 400

    try:
        quantity_kg = validate_quantity(quantity_str)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    # Build record
    record = WasteRecord(
        tracking_code=WasteRecord.generate_tracking_code(),
        department_id=dept.id,
        category_id=cat.id,
        logged_by_id=current_user.id,
        verified_by_id=current_user.id,
        quantity_kg=quantity_kg,
        item_description=item_description or f"Scanned item in {cat.name}",
        image_filename=image_filename or None,
        ai_suggested_category=ai_suggested_category or None,
        ai_confidence=ai_confidence,
        staff_verified=True,
        disposal_status=WasteRecord.STATUS_GENERATED,
        remarks=staff_notes or f"Classified via Smart Assistant (Assigned: {cat.bin_color_name})"
    )
    db.session.add(record)
    db.session.flush()

    # Track correction feedback if staff changed AI prediction
    category_overridden = False
    if ai_suggested_category and ai_suggested_category != cat.code:
        category_overridden = True
        fb = PredictionFeedback(
            waste_record_id=record.id,
            user_id=current_user.id,
            image_filename=image_filename,
            predicted_category=ai_suggested_category,
            predicted_confidence=ai_confidence or 0.0,
            actual_category=cat.code,
            correction_reason=staff_notes or "Staff manually adjusted classification during intake."
        )
        db.session.add(fb)

    db.session.commit()

    return jsonify({
        "success": True,
        "record_id": record.id,
        "tracking_code": record.tracking_code,
        "redirect_url": url_for("waste.view_record", record_id=record.id),
        "category_overridden": category_overridden
    })
