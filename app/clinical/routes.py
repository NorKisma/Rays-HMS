from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.clinical import bp
from app.clinical.forms import VitalForm, PrescriptionForm, PrescriptionItemForm
from app.models import Patient, Doctor, Appointment, PatientVital, Prescription, PrescriptionItem, Product
from app.extensions import db
from app.decorators import permission_required
from datetime import datetime

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
        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=form.doctor_id.data,
            appointment_id=form.appointment_id.data if form.appointment_id.data != 0 else None,
            diagnosis=form.diagnosis.data,
            notes=form.notes.data,
            status='active'
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
                    instructions=instructions[i]
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
