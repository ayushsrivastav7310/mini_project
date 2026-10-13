from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.waste_record import WasteRecord
from app.models.category import WasteCategory
from app.models.department import Department
from app.models.feedback import PredictionFeedback
from app.utils.decorators import admin_required
from app.utils.validators import validate_quantity, sanitize_and_save_image

waste_bp = Blueprint("waste", __name__, url_prefix="/waste")

@waste_bp.route("")
@login_required
def list_records():
    """List waste records with search, multi-field filters, and audit metrics."""
    query = WasteRecord.query

    # Search query
    q = request.args.get("q", "").strip()
    if q:
        search_filter = (
            WasteRecord.tracking_code.ilike(f"%{q}%") |
            WasteRecord.item_description.ilike(f"%{q}%") |
            WasteRecord.dispatch_manifest_no.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    # Filter by category
    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter(WasteRecord.category_id == category_id)

    # Filter by department
    department_id = request.args.get("department_id", type=int)
    if department_id:
        query = query.filter(WasteRecord.department_id == department_id)

    # Filter by status
    status = request.args.get("status", "").strip()
    if status and status in [WasteRecord.STATUS_GENERATED, WasteRecord.STATUS_STORED, WasteRecord.STATUS_DISPATCHED]:
        query = query.filter(WasteRecord.disposal_status == status)

    # Filter by verification
    verified = request.args.get("verified", "").strip()
    if verified == "yes":
        query = query.filter(WasteRecord.staff_verified == True)
    elif verified == "no":
        query = query.filter(WasteRecord.staff_verified == False)

    # Date filters
    date_from = request.args.get("date_from", "").strip()
    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(WasteRecord.created_at >= d_from)
        except ValueError:
            pass

    date_to = request.args.get("date_to", "").strip()
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(WasteRecord.created_at <= d_to)
        except ValueError:
            pass

    records = query.order_by(WasteRecord.created_at.desc()).all()
    filtered_weight = sum(r.quantity_kg for r in records)

    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        "waste/list.html",
        records=records,
        filtered_weight=round(filtered_weight, 2),
        categories=categories,
        departments=departments,
        current_q=q,
        current_category=category_id,
        current_department=department_id,
        current_status=status,
        current_verified=verified,
        current_date_from=date_from,
        current_date_to=date_to
    )


@waste_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_record():
    """Create a new medical waste record (manual entry or AI pre-filled)."""
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    if request.method == "POST":
        department_id = request.form.get("department_id", type=int)
        category_id = request.form.get("category_id", type=int)
        item_description = request.form.get("item_description", "").strip()
        quantity_str = request.form.get("quantity_kg", "").strip()
        remarks = request.form.get("remarks", "").strip()
        staff_verified = bool(request.form.get("staff_verified"))

        # Hidden pre-filled AI values (if routed from AI classifier)
        ai_suggested_category = request.form.get("ai_suggested_category", "").strip() or None
        ai_confidence = request.form.get("ai_confidence", type=float)
        image_filename = request.form.get("image_filename", "").strip() or None

        # Validation
        errors = []
        if not department_id or not Department.query.get(department_id):
            errors.append("Please select a valid hospital department.")
        if not category_id or not WasteCategory.query.get(category_id):
            errors.append("Please select an approved biomedical waste category.")
        if not item_description:
            errors.append("Please provide a description of the waste item.")

        quantity_kg = None
        try:
            quantity_kg = validate_quantity(quantity_str)
        except ValueError as e:
            errors.append(str(e))

        # Handle optional fresh file upload
        if "waste_image" in request.files and request.files["waste_image"].filename != "":
            try:
                saved_filename = sanitize_and_save_image(
                    request.files["waste_image"],
                    current_app.config["UPLOAD_FOLDER"],
                    current_app.config["ALLOWED_EXTENSIONS"]
                )
                image_filename = saved_filename
            except ValueError as e:
                errors.append(str(e))

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "waste/create.html",
                categories=categories,
                departments=departments,
                form_data=request.form
            )

        # Create record
        selected_cat = WasteCategory.query.get(category_id)
        record = WasteRecord(
            tracking_code=WasteRecord.generate_tracking_code(),
            department_id=department_id,
            category_id=category_id,
            logged_by_id=current_user.id,
            verified_by_id=current_user.id if staff_verified else None,
            quantity_kg=quantity_kg,
            item_description=item_description,
            image_filename=image_filename,
            ai_suggested_category=ai_suggested_category,
            ai_confidence=ai_confidence,
            staff_verified=staff_verified,
            disposal_status=WasteRecord.STATUS_GENERATED,
            remarks=remarks
        )
        db.session.add(record)
        db.session.flush()

        # If AI suggestion existed and staff assigned a different category, record feedback
        if ai_suggested_category and ai_suggested_category != selected_cat.code:
            feedback = PredictionFeedback(
                waste_record_id=record.id,
                user_id=current_user.id,
                image_filename=image_filename,
                predicted_category=ai_suggested_category,
                predicted_confidence=ai_confidence or 0.0,
                actual_category=selected_cat.code,
                correction_reason=f"Manual staff correction during waste registration. Staff chose: {selected_cat.name}"
            )
            db.session.add(feedback)

        db.session.commit()
        flash(f"Waste Record #{record.tracking_code} logged successfully in '{selected_cat.name}'.", "success")
        return redirect(url_for("waste.view_record", record_id=record.id))

    # Prepopulate from GET query parameters (e.g. from AI scan result)
    prefill = {
        "category_id": request.args.get("category_id", type=int),
        "ai_suggested_category": request.args.get("ai_suggested_category", ""),
        "ai_confidence": request.args.get("ai_confidence", type=float),
        "image_filename": request.args.get("image_filename", ""),
        "item_description": request.args.get("item_description", "")
    }

    return render_template("waste/create.html", categories=categories, departments=departments, prefill=prefill)


@waste_bp.route("/<int:record_id>")
@login_required
def view_record(record_id: int):
    """Detailed record view with tracking slip and verification badge."""
    record = WasteRecord.query.get_or_404(record_id)
    return render_template("waste/view.html", record=record)


@waste_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def edit_record(record_id: int):
    """Edit existing waste record details."""
    record = WasteRecord.query.get_or_404(record_id)
    categories = WasteCategory.query.filter_by(is_active=True).all()
    departments = Department.query.filter_by(is_active=True).all()

    if request.method == "POST":
        record.department_id = request.form.get("department_id", type=int)
        new_cat_id = request.form.get("category_id", type=int)
        record.item_description = request.form.get("item_description", "").strip()
        quantity_str = request.form.get("quantity_kg", "").strip()
        record.remarks = request.form.get("remarks", "").strip()
        record.staff_verified = bool(request.form.get("staff_verified"))
        if record.staff_verified and not record.verified_by_id:
            record.verified_by_id = current_user.id

        try:
            record.quantity_kg = validate_quantity(quantity_str)
            record.category_id = new_cat_id
            db.session.commit()
            flash(f"Waste Record #{record.tracking_code} updated successfully.", "success")
            return redirect(url_for("waste.view_record", record_id=record.id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("waste/edit.html", record=record, categories=categories, departments=departments)


@waste_bp.route("/<int:record_id>/status", methods=["POST"])
@login_required
def update_status(record_id: int):
    """Update disposal lifecycle status (e.g., dispatch for treatment)."""
    record = WasteRecord.query.get_or_404(record_id)
    new_status = request.form.get("disposal_status", "").strip()
    manifest_no = request.form.get("dispatch_manifest_no", "").strip()
    carrier = request.form.get("dispatch_carrier", "").strip()

    if new_status in [WasteRecord.STATUS_GENERATED, WasteRecord.STATUS_STORED, WasteRecord.STATUS_DISPATCHED]:
        record.disposal_status = new_status
        if manifest_no:
            record.dispatch_manifest_no = manifest_no
        if carrier:
            record.dispatch_carrier = carrier
        db.session.commit()
        flash(f"Status for #{record.tracking_code} updated to '{new_status}'.", "info")
    else:
        flash("Invalid disposal status requested.", "danger")

    return redirect(url_for("waste.view_record", record_id=record.id))


@waste_bp.route("/<int:record_id>/verify", methods=["POST"])
@login_required
def verify_record(record_id: int):
    """Staff verification checkpoint confirmation."""
    record = WasteRecord.query.get_or_404(record_id)
    record.staff_verified = True
    record.verified_by_id = current_user.id
    db.session.commit()
    flash(f"Record #{record.tracking_code} verified by {current_user.full_name}.", "success")
    return redirect(url_for("waste.view_record", record_id=record.id))


@waste_bp.route("/<int:record_id>/delete", methods=["POST"])
@admin_required
def delete_record(record_id: int):
    """Delete a waste record (Administrative privilege required)."""
    record = WasteRecord.query.get_or_404(record_id)
    code = record.tracking_code
    db.session.delete(record)
    db.session.commit()
    flash(f"Record #{code} has been permanently deleted from ledger.", "warning")
    return redirect(url_for("waste.list_records"))
