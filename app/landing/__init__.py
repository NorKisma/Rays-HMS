
from flask import Blueprint

landing_bp = Blueprint("landing", __name__, url_prefix="/")

from . import routes  # register routes after blueprint is created
