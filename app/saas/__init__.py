from flask import Blueprint

saas_bp = Blueprint('saas', __name__, template_folder='templates')

from . import routes
