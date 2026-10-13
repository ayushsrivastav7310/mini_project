from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User authentication route with demo role shortcuts."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        remember = bool(request.form.get("remember"))

        if not username_or_email or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated. Please contact your system administrator.", "danger")
                return render_template("auth/login.html")

            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name} ({user.role})!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            flash("Invalid credentials. Please verify your login details.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/demo-login/<role>")
def demo_login(role: str):
    """Convenience shortcut for evaluators to sign in as Admin or Staff with 1 click."""
    role_map = {
        "admin": "admin",
        "staff": "staff",
        "officer": "officer"
    }
    target_username = role_map.get(role.lower())
    if not target_username:
        flash("Invalid demo role specified.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=target_username).first()
    if user and user.is_active:
        login_user(user)
        flash(f"Authenticated as demo user: {user.full_name} ({user.role})", "info")
        return redirect(url_for("dashboard.index"))
    else:
        flash(f"Demo user '{target_username}' not initialized in database. Run seed script first.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    """Terminate current user session."""
    logout_user()
    flash("You have successfully logged out of the Biomedical Waste System.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    """Display logged in user account details and activity summary."""
    logged_count = current_user.logged_records.count()
    verified_count = current_user.verified_records.count()
    return render_template("auth/profile.html", user=current_user, logged_count=logged_count, verified_count=verified_count)
