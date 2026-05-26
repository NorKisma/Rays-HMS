"""
Appointments API v1 — Tenant-scoped, permission-guarded.
"""
from flask import jsonify, request
from flask_login import login_required, current_user

from app.api import bp
from app.models import Appointment


@bp.route('/v1/appointments', methods=['GET'])
@login_required
def get_appointments():
    """Return upcoming appointments for the current hospital."""
    hid = current_user.hospital_id
    status = request.args.get('status', None, type=str)

    query = Appointment.query.filter_by(hospital_id=hid)

    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.appointment_date.desc()).limit(50).all()

    result = [{
        'id': a.id,
        'patient_name': f"{a.patient.first_name} {a.patient.last_name}" if a.patient else '--',
        'doctor_name': f"{a.doctor.first_name} {a.doctor.last_name}" if a.doctor else '--',
        'date': str(a.appointment_date) if a.appointment_date else '--',
        'status': a.status or 'scheduled',
    } for a in appointments]

    return jsonify({'success': True, 'data': result})
