from flask import jsonify
from app.api import bp
from app.models import Appointment

@bp.route('/v1/appointments', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([{'id': a.id, 'date': a.appointment_date} for a in appointments])
