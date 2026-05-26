from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from app.models import Patient, Appointment
from app.models.reception import VisitorLog, CallLog
from . import bp
from .forms import VisitorLogForm, CallLogForm

@bp.route('/')
@login_required
@permission_required('view_patients') # Using view_patients as standard reception access check
def index():
    # Reception dashboard stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    visitors_today = VisitorLog.query.filter(
        VisitorLog.hospital_id == current_user.hospital_id,
        VisitorLog.check_in_time >= today_start,
        VisitorLog.is_deleted == False
    ).count()
    
    active_visitors = VisitorLog.query.filter(
        VisitorLog.hospital_id == current_user.hospital_id,
        VisitorLog.check_out_time == None,
        VisitorLog.is_deleted == False
    ).count()
    
    calls_today = CallLog.query.filter(
        CallLog.hospital_id == current_user.hospital_id,
        CallLog.created_at >= today_start,
        CallLog.is_deleted == False
    ).count()
    
    # Cards (Check-Ins) metrics
    cards_today = Appointment.query.filter(
        Appointment.hospital_id == current_user.hospital_id,
        Appointment.appointment_date >= today_start,
        Appointment.user_id == current_user.id,
        Appointment.is_deleted == False
    ).count()

    pending_cards = Appointment.query.filter(
        Appointment.hospital_id == current_user.hospital_id,
        Appointment.appointment_date >= today_start,
        Appointment.user_id == current_user.id,
        Appointment.status != 'completed',
        Appointment.is_deleted == False
    ).count()

    today_appointments = Appointment.query.filter(
        Appointment.hospital_id == current_user.hospital_id,
        Appointment.appointment_date >= today_start,
        Appointment.user_id == current_user.id,
        Appointment.is_deleted == False
    ).order_by(Appointment.appointment_date.desc()).all()
    
    recent_visitors = VisitorLog.query.filter_by(
        hospital_id=current_user.hospital_id,
        is_deleted=False
    ).order_by(VisitorLog.check_in_time.desc()).limit(5).all()
    
    recent_calls = CallLog.query.filter_by(
        hospital_id=current_user.hospital_id,
        is_deleted=False
    ).order_by(CallLog.created_at.desc()).limit(5).all()
    
    return render_template(
        'reception/index.html',
        visitors_today=visitors_today,
        active_visitors=active_visitors,
        calls_today=calls_today,
        cards_today=cards_today,
        pending_cards=pending_cards,
        today_appointments=today_appointments,
        recent_visitors=recent_visitors,
        recent_calls=recent_calls
    )

@bp.route('/visitors', methods=['GET', 'POST'])
@login_required
@permission_required('view_patients')
def visitors():
    form = VisitorLogForm()
    
    # Populate patient dropdown with current patients
    patients = Patient.query.filter_by(is_deleted=False, hospital_id=current_user.hospital_id).all()
    form.patient_id.choices = [(0, 'None / Not Visiting Patient')] + [(p.id, f"{p.first_name} {p.last_name} ({p.patient_id})") for p in patients]
    
    if form.validate_on_submit():
        patient_val = form.patient_id.data
        patient_link = patient_val if patient_val > 0 else None
        
        visitor = VisitorLog(
            visitor_name=form.visitor_name.data,
            phone=form.phone.data,
            purpose=form.purpose.data,
            id_type=form.id_type.data or None,
            id_number=form.id_number.data or None,
            patient_id=patient_link,
            temperature=form.temperature.data or None,
            symptoms=form.symptoms.data or None,
            notes=form.notes.data or None,
            recorded_by=current_user.id,
            hospital_id=current_user.hospital_id
        )
        db.session.add(visitor)
        db.session.commit()
        flash('Visitor log recorded successfully!', 'success')
        return redirect(url_for('reception.visitors'))
        
    all_visitors = VisitorLog.query.filter_by(
        hospital_id=current_user.hospital_id,
        is_deleted=False
    ).order_by(VisitorLog.check_in_time.desc()).all()
    
    return render_template('reception/visitors.html', form=form, visitors=all_visitors)

@bp.route('/visitors/<int:id>/checkout', methods=['POST'])
@login_required
@permission_required('view_patients')
def checkout_visitor(id):
    visitor = VisitorLog.query.filter_by(
        id=id,
        hospital_id=current_user.hospital_id,
        is_deleted=False
    ).first_or_404()
    
    visitor.check_out()
    db.session.commit()
    flash(f'Visitor {visitor.visitor_name} checked out successfully!', 'success')
    return redirect(url_for('reception.visitors'))

@bp.route('/calls', methods=['GET', 'POST'])
@login_required
@permission_required('view_patients')
def calls():
    form = CallLogForm()
    
    if form.validate_on_submit():
        call = CallLog(
            caller_name=form.caller_name.data,
            phone=form.phone.data,
            call_type=form.call_type.data,
            call_category=form.call_category.data,
            details=form.details.data,
            action_taken=form.action_taken.data or None,
            follow_up_required=form.follow_up_required.data,
            follow_up_date=form.follow_up_date.data,
            recorded_by=current_user.id,
            hospital_id=current_user.hospital_id
        )
        db.session.add(call)
        db.session.commit()
        flash('Call log recorded successfully!', 'success')
        return redirect(url_for('reception.calls'))
        
    all_calls = CallLog.query.filter_by(
        hospital_id=current_user.hospital_id,
        is_deleted=False
    ).order_by(CallLog.created_at.desc()).all()
    
    return render_template('reception/calls.html', form=form, calls=all_calls)
