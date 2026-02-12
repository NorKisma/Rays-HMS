from flask import Blueprint

bp = Blueprint('doctors', __name__, template_folder='templates')

from . import routes
