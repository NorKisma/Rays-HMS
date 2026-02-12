from flask import Blueprint

bp = Blueprint('billing', __name__, template_folder='templates')

from . import routes
