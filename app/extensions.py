from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session, request

# --------------------------
# Database
# --------------------------
db = SQLAlchemy()
migrate = Migrate()

# --------------------------
# Login manager
# --------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# --------------------------
# Mail
# --------------------------
mail = Mail()

# --------------------------
# Babel (Translations)
# --------------------------
babel = Babel()
LANGUAGES = ['en', 'so']

# New way for Flask-Babel 3.x
def get_locale():
    # First check session, then fall back to Accept-Language
    return session.get('lang') or request.accept_languages.best_match(LANGUAGES)

# --------------------------
# Flask-Limiter
# --------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

def init_limiter(app):
    limiter.init_app(app)
