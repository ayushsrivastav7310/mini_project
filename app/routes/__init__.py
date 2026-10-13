from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.waste import waste_bp
from app.routes.ai import ai_bp
from app.routes.reports import reports_bp
from app.routes.admin import admin_bp

__all__ = ["auth_bp", "dashboard_bp", "waste_bp", "ai_bp", "reports_bp", "admin_bp"]
