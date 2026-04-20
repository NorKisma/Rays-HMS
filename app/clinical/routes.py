from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.clinical import bp
from app.clinical.forms import VitalForm, PrescriptionForm, PrescriptionItemForm
from app.models import (
    Patient, Doctor, Appointment, PatientVital, Prescription,
    PrescriptionItem, Product
)
from app.models.service_price import ServicePrice
from app.models.billing import Billing, BillingItem
from app.extensions import db
from app.decorators import permission_required
from datetime import datetime

@bp.route('/queue')
@login_required
def queue():
    # Fetch appointments/visits in various stages
    # scheduled/waiting_room -> Needs Triage
    # triage_completed -> Needs Doctor
    # consultation_completed -> Needs Billing
    
    waiting_triage = Appointment.query.filter_by(status='waiting_room').order_by(Appointment.created_at.asc()).all()
    waiting_doctor = Appointment.query.filter_by(status='triage_completed').order_by(Appointment.created_at.asc()).all()
    with_doctor = Appointment.query.filter_by(status='consultation').order_by(Appointment.created_at.asc()).all()
    completed = Appointment.query.filter_by(status='completed').order_by(Appointment.updated_at.desc()).limit(10).all()

    return render_template('clinical/queue.html', 
                          waiting_triage=waiting_triage,
                          waiting_doctor=waiting_doctor,
                          with_doctor=with_doctor,
                          completed=completed)

@bp.route('/encounter/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def encounter(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    patient = appointment.patient
    
    # We will use this unified view for both Triage and Consultation
    # Stage depends on appointment.status
    
    vitals = PatientVital.query.filter_by(patient_id=patient.id).order_by(PatientVital.created_at.desc()).first()
    prescriptions = Prescription.query.filter_by(appointment_id=appointment.id).all()
    from app.models.lab import LabTest
    all_lab_tests = LabTest.query.filter_by(is_deleted=False).all()
    
    return render_template('clinical/journey.html', 
                         appointment=appointment, 
                         patient=patient, 
                         vitals=vitals,
                         prescriptions=prescriptions,
                         all_lab_tests=all_lab_tests)

@bp.route('/encounter/<int:appointment_id>/vitals', methods=['POST'])
@login_required
def save_vitals_journey(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    hid = current_user.hospital_id
    # Save vitals to PatientVital model
    vitals = PatientVital(
        patient_id=appointment.patient_id,
        weight=request.form.get('weight'),
        height=request.form.get('height'),
        temperature=request.form.get('temperature'),
        blood_pressure=request.form.get('blood_pressure'),
        heart_rate=request.form.get('heart_rate'),
        respiratory_rate=request.form.get('respiratory_rate'),
        spo2=request.form.get('spo2'),
        note=request.form.get('note'),
        recorded_by=current_user.id,
        hospital_id=hid
    )
    db.session.add(vitals)
    
    # Update appointment snapshot
    appointment.vitals_temperature = vitals.temperature
    appointment.vitals_blood_pressure = vitals.blood_pressure
    appointment.vitals_weight = vitals.weight
    
    # Move status
    appointment.status = 'triage_completed'
    db.session.commit()
    
    flash('Vitals recorded. Patient moved to Doctor Queue.', 'success')
    return redirect(url_for('clinical.queue'))

@bp.route('/encounter/<int:appointment_id>/complete', methods=['POST'])
@login_required
def complete_encounter(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    hid = current_user.hospital_id
    
    # Process Lab Tests
    selected_lab_ids = request.form.getlist('lab_tests[]')
    from app.models.lab import LabTest, LabRequest
    
    # Initialize Billing if needed
    billing = Billing.query.filter_by(appointment_id=appointment.id).first()
    if not billing:
        invoice_num = f"INV-{datetime.now().strftime('%y%m%d')}-{appointment.id:04d}"
        billing = Billing(
            invoice_number=invoice_num,
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            total_amount=0,
            net_amount=0,
            balance_amount=0,
            hospital_id=hid
        )
        db.session.add(billing)
        db.session.flush()

    total_added = 0
    for test_id in selected_lab_ids:
        test = LabTest.query.get(test_id)
        if test:
            lr = LabRequest(
                appointment_id=appointment.id,
                test_name=test.name,
                status='pending_payment',
                hospital_id=hid
            )
            db.session.add(lr)
            
            # Add to Billing
            bi = BillingItem(
                billing_id=billing.id,
                description=f"Lab Test: {test.name}",
                quantity=1,
                unit_price=test.price,
                subtotal=test.price,
                hospital_id=hid
            )
            db.session.add(bi)
            total_added += test.price

    # Update Billing totals
    billing.total_amount = float(billing.total_amount or 0) + float(total_added)
    billing.net_amount = billing.total_amount
    billing.balance_amount = billing.net_amount - float(billing.paid_amount or 0)

    # Update appointment data
    appointment.diagnosis = request.form.get('diagnosis')
    appointment.status = 'completed'
    appointment.updated_at = datetime.now()
    
    db.session.commit()
    flash(f'Encounter completed. Invoice generated for {appointment.patient.full_name}.', 'success')
    return redirect(url_for('clinical.queue'))

@bp.route('/patient/<int:patient_id>/vitals/add', methods=['GET', 'POST'])
@login_required
def add_vitals(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = VitalForm()
    if form.validate_on_submit():
        vitals = PatientVital(
            patient_id=patient.id,
            weight=form.weight.data,
            height=form.height.data,
            temperature=form.temperature.data,
            blood_pressure=form.blood_pressure.data,
            heart_rate=form.heart_rate.data,
            respiratory_rate=form.respiratory_rate.data,
            spo2=form.spo2.data,
            note=form.note.data,
            recorded_by=current_user.id
        )
        db.session.add(vitals)
        db.session.commit()
        flash('Vitals recorded successfully!', 'success')
        return redirect(url_for('patients.view', id=patient.id))
    
    return render_template('clinical/add_vitals.html', form=form, patient=patient)

@bp.route('/patient/<int:patient_id>/prescription/add', methods=['GET', 'POST'])
@login_required
def add_prescription(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PrescriptionForm()
    
    # Populate choices
    doctors = Doctor.query.filter_by(deleted_at=None).all()
    form.doctor_id.choices = [(d.id, f"{d.first_name} {d.last_name} ({d.specialization})") for d in doctors]
    
    appointments = Appointment.query.filter_by(patient_id=patient.id, deleted_at=None).order_by(Appointment.appointment_date.desc()).all()
    form.appointment_id.choices = [(0, 'None')] + [(a.id, f"{a.appointment_date.strftime('%Y-%m-%d')} - {a.reason}") for a in appointments]

    if form.validate_on_submit():
        hid = current_user.hospital_id
        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=form.doctor_id.data,
            appointment_id=form.appointment_id.data if form.appointment_id.data != 0 else None,
            diagnosis=form.diagnosis.data,
            notes=form.notes.data,
            status='active',
            hospital_id=hid
        )
        db.session.add(prescription)
        db.session.flush() # Get id before commit
        
        # Handle items from request.form (dynamic items)
        med_names = request.form.getlist('medicine_name[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('instructions[]')
        
        for i in range(len(med_names)):
            if med_names[i]:
                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=med_names[i],
                    dosage=dosages[i],
                    frequency=frequencies[i],
                    duration=durations[i],
                    instructions=instructions[i],
                    hospital_id=hid
                )
                db.session.add(item)
        
        db.session.commit()
        flash('Prescription created successfully!', 'success')
        return redirect(url_for('patients.view', id=patient.id))

    return render_template('clinical/add_prescription.html', form=form, patient=patient)

@bp.route('/prescription/<int:id>/print')
@login_required
def print_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    return render_template('clinical/print_prescription.html', p=prescription)

@bp.route('/patient/<int:patient_id>/triage', methods=['GET', 'POST'])
@login_required
def add_triage(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        triage = Triage(
            patient_id=patient.id,
            priority_level=request.form.get('priority_level'),
            symptoms=request.form.get('symptoms'),
            triage_notes=request.form.get('triage_notes'),
            temp=request.form.get('temp'),
            bp=request.form.get('bp'),
            pulse=request.form.get('pulse'),
            recorded_by=current_user.id
        )
        db.session.add(triage)
        db.session.commit()
        flash('Patient triaged successfully!', 'success')
        return redirect(url_for('patients.view', id=patient.id))
    
    return render_template('clinical/add_triage.html', patient=patient)

@bp.route('/patient/<int:patient_id>/condition/add', methods=['GET', 'POST'])
@login_required
def add_condition(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        condition = ChronicCondition(
            patient_id=patient.id,
            condition_name=request.form.get('condition_name'),
            on_set_date=datetime.strptime(request.form.get('on_set_date'), '%Y-%m-%d').date() if request.form.get('on_set_date') else None,
            severity=request.form.get('severity'),
            status=request.form.get('status'),
            notes=request.form.get('notes')
        )
        db.session.add(condition)
        db.session.commit()
        flash('Chronic condition added!', 'success')
        return redirect(url_for('patients.view', id=patient.id))
    
    return render_template('clinical/add_condition.html', patient=patient)

@bp.route('/clinical/ai-suggest', methods=['POST'])
@login_required
def ai_suggest():
    symptoms = request.json.get('symptoms', '').lower()
    
    # Simple rule-based logic for demonstration
    suggestions = []
    if 'fever' in symptoms or 'headache' in symptoms:
        suggestions.append('Malaria (High Priority)')
        suggestions.append('Common Cold')
    if 'cough' in symptoms or 'breath' in symptoms:
        suggestions.append('Lower Respiratory Tract Infection')
        suggestions.append('Pneumonia Assessment Required')
    if 'pain' in symptoms and 'stomach' in symptoms:
        suggestions.append('Gastroenteritis')
        suggestions.append('Peptic Ulcer Disease')
    
    if not suggestions:
        suggestions.append('General Symptomatic Assessment')
        
    return jsonify({'suggestions': suggestions})
