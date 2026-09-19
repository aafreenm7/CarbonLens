import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration for CarbonLens."""

    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "dev-insecure-carbonlens-secret-key-2026-btech-project"
    )

    # Database: Default to local SQLite, easily switchable to PostgreSQL via DATABASE_URL
    _db_url = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'carbonlens.db'}"
    )
    # Compatibility fix for Supabase / Heroku postgres:// prefix
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security & Sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # Uploads and limits
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH_MB", 16)
    ) * 1024 * 1024  # 16 MB limit
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    EXPORTS_FOLDER = BASE_DIR / "exports"
    CHARTS_FOLDER = BASE_DIR / "static" / "generated_charts"
    DATA_FOLDER = BASE_DIR / "data"

    ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

    # Grid & Emission baseline constants
    DEFAULT_GRID_FACTOR_KG = 0.710  # kgCO2e/kWh (Central Electricity Authority India FY24-25)


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
