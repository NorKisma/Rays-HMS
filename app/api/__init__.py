from flask import Blueprint

bp = Blueprint('api', __name__)

from .v1 import patients, appointments, dashboard
