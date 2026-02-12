from flask import Blueprint

bp = Blueprint('lab', __name__, 
               url_prefix='/lab',
               template_folder='templates')

from . import routes
