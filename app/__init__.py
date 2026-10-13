import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, send_from_directory, abort
from config import config_by_name
from app.extensions import db, login_manager
from app.models.user import User

def create_app(config_name: str = "development") -> Flask:
    """Application factory for the Medical Waste Segregation System."""
    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # Ensure instance and upload directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Configure Logging
    _configure_logging(app)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.waste import waste_bp
    from app.routes.ai import ai_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(waste_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Serve uploaded images
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Register Global Context Processors
    @app.context_processor
    def inject_global_template_vars():
        return {
            "hospital_name": app.config.get("HOSPITAL_NAME"),
            "hospital_code": app.config.get("HOSPITAL_CODE"),
            "disclaimer_text": app.config.get("REGULATORY_DISCLAIMER"),
            "current_year": 2026
        }

    # Register Error Handlers
    _register_error_handlers(app)

    return app


def _configure_logging(app: Flask):
    """Setup rotating log file and standard output logger."""
    if not app.debug or os.environ.get("FLASK_ENV") == "production":
        log_dir = os.path.join(app.root_path, "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "medical_waste.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Smart Medical Waste Management System startup initialized.")


def _register_error_handlers(app: Flask):
    """Register custom error pages for uniform healthcare styling."""
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Internal Server Error: {str(error)}")
        return render_template("errors/500.html", error=error), 500
