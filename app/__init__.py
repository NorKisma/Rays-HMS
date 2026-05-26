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
    from .clinical import bp as clinical_bp
    from .ipd import bp as ipd_bp
    from .saas import saas_bp

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
    from .reception import bp as reception_bp
    app.register_blueprint(accounting_bp, url_prefix="/accounting")
    app.register_blueprint(reception_bp, url_prefix="/reception")
    app.register_blueprint(clinical_bp, url_prefix="/clinical")
    app.register_blueprint(ipd_bp, url_prefix="/ipd")
    app.register_blueprint(saas_bp, url_prefix="/saas")

    # Make instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Global Jinja Filters
    @app.template_filter('format_date')
    def format_date(value, format='%d %b, %Y'):
        if value is None:
            return ""
        
        # Handle invalid 0000-00-00 
        val_str = str(value)
        if val_str.startswith('0000-00-00'):
            return "New Account"

        if isinstance(value, str):
            try:
                from dateutil import parser
                value = parser.parse(value)
            except:
                try:
                    from datetime import datetime
                    value = datetime.strptime(value.split('.')[0], '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        value = datetime.strptime(value.split(' ')[0], '%Y-%m-%d')
                    except:
                        return value
        try:
            return value.strftime(format)
        except:
            return str(value)

    return app
