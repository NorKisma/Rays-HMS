import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from .extensions import db, migrate, login_manager, mail, babel, limiter, get_locale
from .config import get_config
from .models import User

# ---------------------------
# User loader for flask-login
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# ---------------------------
# Create Flask app
# ---------------------------
def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=False)

    # Load config
    cfg = get_config(os.getenv("FLASK_ENV", "development"))
    app.config.from_object(cfg)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    babel.init_app(app, locale_selector=get_locale)  # <-- new 3.x syntax

    # ---------------------------
    # Register blueprints
    # ---------------------------
    from app.landing.routes import landing_bp
    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .patients import bp as patients_bp
    from .doctors import bp as doctors_bp
    from .appointments import bp as appointments_bp
    from .billing import bp as billing_bp
    from .inventory import bp as inventory_bp
    from .sales import bp as sales_bp
    from .api import bp as api_bp
    from .lab import bp as lab_bp
    from .settings import bp as settings_bp

    # REGISTER BLUEPRINTS
    app.register_blueprint(landing_bp, url_prefix="/")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(doctors_bp, url_prefix="/doctors")
    app.register_blueprint(appointments_bp, url_prefix="/appointments")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(sales_bp, url_prefix="/sales")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(lab_bp, url_prefix="/lab")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    from .accounting import bp as accounting_bp
    app.register_blueprint(accounting_bp, url_prefix="/accounting")

    # Make instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    return app
