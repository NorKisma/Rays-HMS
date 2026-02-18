from flask import Blueprint

bp = Blueprint('clinical', __name__, template_folder='templates')

from . import routes
