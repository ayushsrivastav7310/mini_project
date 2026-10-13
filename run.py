import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from seed import seed_database

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

@app.cli.command("init-db")
def init_db_command():
    """CLI command to initialize and seed the database."""
    with app.app_context():
        seed_database()
        print("Database successfully initialized and seeded.")

def ensure_initialized():
    """Auto-initialize database if not present on first run."""
    with app.app_context():
        db_file = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite:///" in db_file and not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path, exist_ok=True)
        # Check if tables exist
        try:
            from app.models.category import WasteCategory
            if WasteCategory.query.count() == 0:
                print("First run detected: automatically initializing database and seeding standard BMW rules...")
                seed_database()
        except Exception:
            print("Creating database tables and seeding standard BMW rules...")
            seed_database()

if __name__ == "__main__":
    ensure_initialized()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("DEBUG", "True").lower() in ("true", "1")
    print(f"\n=======================================================")
    print(f" AI-Based Smart Medical Waste Segregation & Management")
    print(f" Hospital Portal: http://{host}:{port}")
    print(f" Educational Prototype | BMW Rules 2016 Compliant")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=debug)
