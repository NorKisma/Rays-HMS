
from flask import Blueprint

bp = Blueprint('accounting', __name__, template_folder='templates', url_prefix='/accounting')

from . import routes
