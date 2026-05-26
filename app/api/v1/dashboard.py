"""
Dashboard API — Real-time stats endpoint for AJAX-powered dashboard.
All queries are hospital_id scoped (multi-tenant safe).
"""
from flask import jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime
from sqlalchemy import func, extract

from app.api import bp
from app.models import (
    Patient, Doctor, Appointment, Inventory, Billing, BillingItem,
    Batch, Triage, Admission, LabRequest, Sale, SaleItem
)
from app.extensions import db


@bp.route('/v1/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    """Return core KPI stats for the logged-in user's hospital."""
    hid = current_user.hospital_id
    today = date.today()
    ninety_days = today + timedelta(days=90)

    stats = {
        'total_patients': Patient.query.filter_by(hospital_id=hid).count(),
        'total_doctors': Doctor.query.filter_by(hospital_id=hid).count(),
        'pending_appointments': Appointment.query.filter_by(
            hospital_id=hid, status='scheduled'
        ).count(),
        'low_stock': Inventory.query.filter_by(hospital_id=hid).filter(
            Inventory.quantity <= 10
        ).count(),
        'expiring_soon': Batch.query.filter(
            Batch.hospital_id == hid,
            Batch.expiry_date.between(today, ninety_days),
            Batch.is_deleted == False
        ).count(),
        'unpaid_bills': Billing.query.filter_by(
            hospital_id=hid, payment_status='unpaid'
        ).count(),
        'lab_pending': LabRequest.query.filter_by(
            hospital_id=hid, status='pending'
        ).count(),
        'emergency_queue': Triage.query.filter_by(
            hospital_id=hid, status='pending'
        ).count(),
        'active_admissions': Admission.query.filter_by(
            hospital_id=hid, status='admitted'
        ).count(),
    }

    return jsonify({'success': True, 'data': stats})


@bp.route('/v1/dashboard/recent-patients', methods=['GET'])
@login_required
def dashboard_recent_patients():
    """Return latest 8 registered patients."""
    hid = current_user.hospital_id
    patients = Patient.query.filter_by(hospital_id=hid)\
        .order_by(Patient.created_at.desc()).limit(8).all()

    result = []
    for p in patients:
        result.append({
            'id': p.id,
            'patient_id': p.patient_id,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'phone': p.phone or '--',
            'created_at': p.created_at.strftime('%d %b %Y') if p.created_at else '--',
            'initials': f"{p.first_name[0]}{p.last_name[0]}" if p.first_name and p.last_name else '??'
        })

    return jsonify({'success': True, 'data': result})


@bp.route('/v1/dashboard/revenue-chart', methods=['GET'])
@login_required
def dashboard_revenue_chart():
    """Return monthly revenue data for the last 6 months."""
    hid = current_user.hospital_id
    today = date.today()
    months = []
    labels = []
    values = []

    for i in range(5, -1, -1):
        # Calculate month start
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    for y, m in months:
        labels.append(datetime(y, m, 1).strftime('%b %Y'))
        total = db.session.query(func.coalesce(func.sum(Billing.total_amount), 0))\
            .filter(
                Billing.hospital_id == hid,
                extract('year', Billing.created_at) == y,
                extract('month', Billing.created_at) == m
            ).scalar()
        values.append(float(total or 0))

    return jsonify({
        'success': True,
        'data': {'labels': labels, 'values': values}
    })


@bp.route('/v1/dashboard/department-load', methods=['GET'])
@login_required
def dashboard_department_load():
    """Return appointment counts grouped by doctor specialization."""
    hid = current_user.hospital_id

    results = db.session.query(
        Doctor.specialization,
        func.count(Appointment.id)
    ).join(
        Appointment, Appointment.doctor_id == Doctor.id
    ).filter(
        Doctor.hospital_id == hid,
        Appointment.status == 'scheduled'
    ).group_by(Doctor.specialization).all()

    labels = []
    values = []
    for spec, count in results:
        labels.append(spec or 'General')
        values.append(count)

    # Fill with defaults if no data
    if not labels:
        labels = ['General', 'Surgery', 'Pediatrics', 'OB/GYN']
        values = [0, 0, 0, 0]

    return jsonify({
        'success': True,
        'data': {'labels': labels, 'values': values}
    })


@bp.route('/v1/dashboard/activity-feed', methods=['GET'])
@login_required
def dashboard_activity_feed():
    """Return recent system activity for the hospital."""
    hid = current_user.hospital_id
    feed = []

    # Recent admissions
    admissions = Admission.query.filter_by(hospital_id=hid)\
        .order_by(Admission.created_at.desc()).limit(3).all()
    for a in admissions:
        patient_name = f"{a.patient.first_name} {a.patient.last_name}" if a.patient else "Unknown"
        feed.append({
            'type': 'admission',
            'icon': 'fa-procedures',
            'color': 'info',
            'message': f"{patient_name} admitted",
            'time': a.created_at.strftime('%H:%M') if a.created_at else '--'
        })

    # Recent lab requests
    labs = LabRequest.query.filter_by(hospital_id=hid)\
        .order_by(LabRequest.created_at.desc()).limit(3).all()
    for l in labs:
        patient_name = f"{l.patient.first_name} {l.patient.last_name}" if l.patient else "Unknown"
        feed.append({
            'type': 'lab',
            'icon': 'fa-vials',
            'color': 'warning',
            'message': f"Lab request for {patient_name}",
            'time': l.created_at.strftime('%H:%M') if l.created_at else '--'
        })

    # Sort by time (most recent first) and limit
    feed.sort(key=lambda x: x['time'], reverse=True)
    return jsonify({'success': True, 'data': feed[:6]})
