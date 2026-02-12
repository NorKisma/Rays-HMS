from flask import jsonify
from app.api import bp
from app.models import Patient

@bp.route('/v1/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([{'id': p.id, 'name': f"{p.first_name} {p.last_name}"} for p in patients])
