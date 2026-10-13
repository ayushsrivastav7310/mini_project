from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Core application extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Login manager configuration
login_manager.login_view = "auth.login"
login_manager.login_message = "Please authenticate to access the medical waste management system."
login_manager.login_message_category = "warning"
