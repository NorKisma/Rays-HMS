import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def build_mysql_uri():
    """
    Build SQLAlchemy MySQL URI safely from environment variables.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    name = os.getenv("DB_NAME", "hms_db")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


class BaseConfig:
    """Base configuration shared across all environments"""

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis for caching and rate limiting
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Rate limiting rules
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200/day;50/hour")

    # Internationalization
    BABEL_DEFAULT_LOCALE = os.getenv("BABEL_DEFAULT_LOCALE", "en")
    BABEL_DEFAULT_TIMEZONE = os.getenv("BABEL_DEFAULT_TIMEZONE", "Africa/Mogadishu")

    # Email settings
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT") or 25)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() in ("1", "true", "yes")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() in ("1", "true", "yes")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # Session
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")


class DevelopmentConfig(BaseConfig):
    DEBUG = True

    # Allow fallback to SQLite for dev convenience
    try:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or build_mysql_uri()
    except Exception:
        SQLALCHEMY_DATABASE_URI = "sqlite:///instance/app.db"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False

    # Test DB fallback
    try:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or build_mysql_uri()
    except Exception:
        SQLALCHEMY_DATABASE_URI = "sqlite:///instance/test.db"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or build_mysql_uri()

    # Production cookie security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def get_config(name: str = None):
    """
    Return the appropriate configuration class.
    Default: development
    """
    name = (name or "development").lower()

    if name in ("production", "prod"):
        return ProductionConfig

    if name in ("testing", "test"):
        return TestingConfig

    return DevelopmentConfig
