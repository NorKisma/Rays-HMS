from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.ipd import bp
from app.models import Ward, Bed, Admission, Patient, Doctor
from app.extensions import db
from datetime import datetime

@bp.route('/wards')
@login_required
def wards():
    all_wards = Ward.query.filter_by(is_deleted=False).all()
    return render_template('ipd/wards.html', wards=all_wards)

@bp.route('/wards/<int:id>')
@login_required
def ward_details(id):
    ward = Ward.query.get_or_404(id)
    return render_template('ipd/ward_details.html', ward=ward)

@bp.route('/admissions')
@login_required
def admissions():
    active_admissions = Admission.query.filter_by(status='admitted').all()
    return render_template('ipd/admissions.html', admissions=active_admissions, now=datetime.utcnow())

@bp.route('/admission/new', methods=['GET', 'POST'])
@login_required
def new_admission():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        bed_id = request.form.get('bed_id')
        doctor_id = request.form.get('doctor_id')
        reason = request.form.get('reason')
        
        admission = Admission(
            patient_id=patient_id,
            bed_id=bed_id,
            doctor_id=doctor_id,
            reason=reason,
            status='admitted'
        )
        # Update bed status
        bed = Bed.query.get(bed_id)
        if bed:
            bed.status = 'occupied'
            
        db.session.add(admission)
        db.session.commit()
        flash('Patient admitted successfully!', 'success')
        return redirect(url_for('ipd.admissions'))
        
    patients = Patient.query.filter_by(is_deleted=False).all()
    doctors = Doctor.query.filter_by(is_deleted=False).all()
    available_beds = Bed.query.filter_by(status='available', is_deleted=False).all()
    return render_template('ipd/new_admission.html', patients=patients, doctors=doctors, beds=available_beds)

@bp.route('/discharge/<int:id>', methods=['POST'])
@login_required
def discharge(id):
    admission = Admission.query.get_or_404(id)
    admission.status = 'discharged'
    admission.discharge_date = datetime.utcnow()
    
    # Free up the bed
    bed = Bed.query.get(admission.bed_id)
    if bed:
        bed.status = 'available'
        
    db.session.commit()
    flash('Patient discharged successfully!', 'success')
    return redirect(url_for('ipd.admissions'))

@bp.route('/transfer/<int:id>', methods=['GET', 'POST'])
@login_required
def transfer(id):
    admission = Admission.query.get_or_404(id)
    if request.method == 'POST':
        new_bed_id = request.form.get('new_bed_id')
        
        # 1. Free the old bed
        old_bed = Bed.query.get(admission.bed_id)
        if old_bed:
            old_bed.status = 'available'
            
        # 2. Occupy the new bed
        new_bed = Bed.query.get(new_bed_id)
        if new_bed:
            new_bed.status = 'occupied'
            admission.bed_id = new_bed.id
            
        db.session.commit()
        flash('Patient transferred successfully!', 'success')
        return redirect(url_for('ipd.admissions'))
        
    available_beds = Bed.query.filter_by(status='available', is_deleted=False).all()
    return render_template('ipd/transfer.html', admission=admission, beds=available_beds)

@bp.route('/admission/<int:id>/notes', methods=['GET', 'POST'])
@login_required
def admission_notes(id):
    admission = Admission.query.get_or_404(id)
    if request.method == 'POST':
        note = NursingNote(
            admission_id=id,
            staff_id=current_user.id,
            note_content=request.form.get('note_content'),
            temperature=request.form.get('temp'),
            blood_pressure=request.form.get('bp'),
            pulse_rate=request.form.get('pulse')
        )
        db.session.add(note)
        db.session.commit()
        flash('Nursing note added!', 'success')
        return redirect(url_for('ipd.admission_notes', id=id))
        
    return render_template('ipd/admission_notes.html', admission=admission)
