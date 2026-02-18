from flask import Blueprint, render_template, session, redirect, request, url_for, flash
from flask_login import login_required, current_user
from ..decorators import role_required, permission_required
from ..utils import log_action

# --------------------------
# Blueprint
# --------------------------
bp = Blueprint("main", __name__, template_folder='templates')


# --------------------------
# Dashboard
# --------------------------
@bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import Patient, Doctor, Appointment, Inventory, Billing, Batch, Triage, Admission, LabRequest
    from datetime import date, timedelta
    today = date.today()
    ninety_days = today + timedelta(days=90)
    
    stats = {
        'total_patients': Patient.query.count(),
        'total_doctors': Doctor.query.count(),
        'pending_appointments': Appointment.query.filter_by(status='scheduled').count(),
        'low_stock': Inventory.query.filter(Inventory.quantity <= 10).count(),
        'expiring_soon': Batch.query.filter(Batch.expiry_date.between(today, ninety_days), Batch.is_deleted == False).count(),
        'unpaid_bills': Billing.query.filter_by(payment_status='unpaid').count(),
        'lab_pending': LabRequest.query.filter_by(status='pending').count(),
        'emergency_queue': Triage.query.filter_by(status='pending').count(),
        'active_admissions': Admission.query.filter_by(status='admitted').count(),
        'recent_patients': Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    }
    
    return render_template('main/dashboard.html', user=current_user, **stats)


# --------------------------
# Settings (Admin only with permission)
# --------------------------
@bp.route('/settings')
@login_required
@permission_required('update_settings')
def settings():
    """
    Admin-only settings page.
    """
    log_action("Accessed settings page")
    return render_template("main/settings.html", user=current_user)


# --------------------------
# Language Selector
# --------------------------
@bp.route("/set_language/<lang_code>")
def set_language(lang_code):
    """
    Update session language and redirect back to previous page.
    """
    if lang_code in ['en', 'so']:
        session['lang'] = lang_code
        flash(f"Language changed to {lang_code.upper()}", "success")
    return redirect(request.referrer or url_for('main.dashboard'))
