from flask import Blueprint

bp = Blueprint('inventory', __name__, template_folder='templates')

from . import routes
