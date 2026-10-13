from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.extensions import db
from app.models.category import WasteCategory
from app.models.department import Department
from app.models.user import User
from app.models.feedback import PredictionFeedback
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# --- CATEGORY MANAGEMENT ---
@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    """Configurable Biomedical Waste Categories under BMW Rules 2016."""
    if request.method == "POST":
        category_id = request.form.get("category_id", type=int)
        name = request.form.get("name", "").strip()
        bin_color_name = request.form.get("bin_color_name", "").strip()
        bin_color_hex = request.form.get("bin_color_hex", "").strip() or "#ffc107"
        container_type = request.form.get("container_type", "").strip()
        treatment_method = request.form.get("treatment_method", "").strip()
        permitted_items = request.form.get("permitted_items", "").strip()
        prohibited_items = request.form.get("prohibited_items", "").strip()

        if category_id:
            # Edit existing
            cat = WasteCategory.query.get_or_404(category_id)
            cat.name = name
            cat.bin_color_name = bin_color_name
            cat.bin_color_hex = bin_color_hex
            cat.container_type = container_type
            cat.treatment_method = treatment_method
            cat.permitted_items = permitted_items
            cat.prohibited_items = prohibited_items
            flash(f"Category '{cat.name}' updated successfully.", "success")
        else:
            # Create new
            code = request.form.get("code", "").strip().upper()
            if not code or WasteCategory.query.filter_by(code=code).first():
                flash("Category code is missing or already exists.", "danger")
                return redirect(url_for("admin.categories"))
            cat = WasteCategory(
                code=code,
                name=name,
                bin_color_name=bin_color_name,
                bin_color_hex=bin_color_hex,
                badge_class="bg-info text-dark",
                container_type=container_type,
                treatment_method=treatment_method,
                permitted_items=permitted_items,
                prohibited_items=prohibited_items
            )
            db.session.add(cat)
            flash(f"New category '{cat.name}' registered.", "success")

        db.session.commit()
        return redirect(url_for("admin.categories"))

    cats = WasteCategory.query.order_by(WasteCategory.id).all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categories/<int:cat_id>/toggle", methods=["POST"])
@admin_required
def toggle_category(cat_id: int):
    """Enable or disable category in hospital selection."""
    cat = WasteCategory.query.get_or_404(cat_id)
    cat.is_active = not cat.is_active
    db.session.commit()
    flash(f"Category '{cat.name}' active status set to {cat.is_active}.", "info")
    return redirect(url_for("admin.categories"))


# --- DEPARTMENT MANAGEMENT ---
@admin_bp.route("/departments", methods=["GET", "POST"])
@admin_required
def departments():
    """Hospital department registration and management."""
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        floor = request.form.get("floor_location", "").strip()
        contact = request.form.get("contact_person", "").strip()

        if not code or not name:
            flash("Department Code and Name are mandatory.", "danger")
        elif Department.query.filter_by(code=code).first():
            flash(f"Department with code '{code}' already exists.", "danger")
        else:
            dept = Department(code=code, name=name, floor_location=floor, contact_person=contact)
            db.session.add(dept)
            db.session.commit()
            flash(f"Department '{dept.name}' added successfully.", "success")

        return redirect(url_for("admin.departments"))

    depts = Department.query.order_by(Department.name).all()
    return render_template("admin/departments.html", departments=depts)


# --- USER MANAGEMENT ---
@admin_bp.route("/users")
@admin_required
def users():
    """User roster and access role overview."""
    all_users = User.query.order_by(User.id).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id: int):
    """Activate or deactivate user credentials."""
    target_user = User.query.get_or_404(user_id)
    target_user.is_active = not target_user.is_active
    db.session.commit()
    flash(f"User {target_user.username} status toggled to {'Active' if target_user.is_active else 'Deactivated'}.", "info")
    return redirect(url_for("admin.users"))


# --- AI PREDICTION CORRECTION AUDIT ---
@admin_bp.route("/feedback")
@admin_required
def feedback():
    """Review staff overrides of AI predictions for model monitoring."""
    feedbacks = PredictionFeedback.query.order_by(PredictionFeedback.created_at.desc()).all()
    return render_template("admin/feedback.html", feedbacks=feedbacks)
