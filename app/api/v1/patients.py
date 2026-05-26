"""
Patients API v1 — Tenant-scoped, permission-guarded.
"""
from flask import jsonify, request
from flask_login import login_required, current_user

from app.api import bp
from app.models import Patient


@bp.route('/v1/patients', methods=['GET'])
@login_required
def get_patients():
    """Return paginated patient list, scoped to current hospital."""
    hid = current_user.hospital_id
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('q', '', type=str).strip()

    query = Patient.query.filter_by(hospital_id=hid)

    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.patient_id.ilike(f'%{search}%'))
        )

    pagination = query.order_by(Patient.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    patients = [{
        'id': p.id,
        'patient_id': p.patient_id,
        'name': f"{p.first_name} {p.last_name}",
        'phone': p.phone or '--',
        'gender': getattr(p, 'gender', '--'),
        'created_at': p.created_at.strftime('%d %b %Y') if p.created_at else '--',
    } for p in pagination.items]

    return jsonify({
        'success': True,
        'data': patients,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }
    })
