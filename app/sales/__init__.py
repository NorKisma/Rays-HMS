from flask import Blueprint

bp = Blueprint('sales', __name__, template_folder='templates')

from . import routes
