from flask import Blueprint

bp = Blueprint('ipd', __name__, template_folder='templates')

from . import routes
