from flask import g
from flask_login import current_user

def get_current_hospital_id():
    """Returns the hospital_id of the currently logged-in user."""
    if current_user.is_authenticated:
        return current_user.hospital_id
    return getattr(g, 'hospital_id', None)

def set_current_hospital_id(hospital_id):
    """Sets the hospital_id in the application context."""
    g.hospital_id = hospital_id
