from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Ensure that the authenticated user holds the ADMIN role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this administrative resource.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin_user:
            flash("Administrative authorization required to access this resource.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Ensure that the authenticated user has at least STAFF or ADMIN access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this clinical resource.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
