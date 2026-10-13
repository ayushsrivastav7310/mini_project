import os
from pathlib import Path

# Base project root directory
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-medical-waste-segregation-2026")
    
    # SQLite Database Default
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'instance' / 'medical_waste.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = BASE_DIR / os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # AI Classifier settings
    AI_CONFIDENCE_THRESHOLD = float(os.environ.get("AI_CONFIDENCE_THRESHOLD", 0.75))
    AI_MODEL_PATH = BASE_DIR / os.environ.get("AI_MODEL_PATH", "models/mobilenetv2_medical_waste.h5")
    
    # Hospital / Institution Metadata
    HOSPITAL_NAME = os.environ.get("HOSPITAL_NAME", "Lifeline Multispecialty Hospital")
    HOSPITAL_CODE = os.environ.get("HOSPITAL_CODE", "LMH-BMW-REG-4821")
    HOSPITAL_ADDRESS = os.environ.get("HOSPITAL_ADDRESS", "Healthcare City, New Delhi - 110001")
    PCB_REGISTRATION_NO = os.environ.get("HOSPITAL_POLLUTION_CONTROL_BOARD_ID", "SPCB/BMW/2026/0942")
    
    # Safety Disclaimer
    REGULATORY_DISCLAIMER = (
        "EDUCATIONAL PROTOTYPE NOTICE: This system provides guidance based on Indian Bio-Medical "
        "Waste Management Rules (2016). In accordance with institutional safety mandates, all waste "
        "segregations must be physically verified by authorized healthcare staff prior to disposal."
    )

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    UPLOAD_FOLDER = BASE_DIR / "tests" / "test_uploads"

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Enforce secure secret key in production
    SECRET_KEY = os.environ.get("SECRET_KEY")

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
