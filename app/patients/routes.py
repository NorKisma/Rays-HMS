from datetime import datetime, date, timedelta
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from . import bp
from decimal import Decimal

from app.models import Patient, Doctor, Appointment, Billing, BillingItem, SystemSetting
from .forms import PatientForm, CheckInForm

@bp.route('/')
@login_required
@permission_required('view_patients')
def index():
    patients = Patient.query.filter_by(is_deleted=False).all()
    return render_template('patients/index.html', patients=patients)

@bp.route('/checkin/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@permission_required('add_appointments') # Assuming this permission exists or uses a similar one
def checkin(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = CheckInForm()
    
    # Populate doctors
    doctors = Doctor.query.filter_by(is_deleted=False).all()
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name} ({d.specialization})") for d in doctors]
    
    if form.validate_on_submit():
        doctor = Doctor.query.get(form.doctor_id.data)

        # 1. Create Invoice for Card/Consultation
        default_fee = Decimal("5.00")
        raw_fee = SystemSetting.get("billing.card_fee", default_fee)
        try:
            card_fee = float(Decimal(str(raw_fee)))
        except Exception:
            card_fee = float(default_fee)
        
        # Generate Invoice Number
        import time
        inv_num = f"INV-{int(time.time())}"
        
        billing = Billing(
            invoice_number=inv_num,
            patient_id=patient.id,
            total_amount=card_fee,
            net_amount=card_fee,
            balance_amount=card_fee,
            payment_status='unpaid'
        )
        db.session.add(billing)
        db.session.flush() # Get ID
        
        item = BillingItem(
            billing_id=billing.id,
            description="Consultation Card / Registration Fee",
            quantity=1,
            unit_price=card_fee,
            subtotal=card_fee
        )
        db.session.add(item)
        
        # 2. Create Appointment
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        apt_num = f"APT-{patient.id}-{timestamp}"
        
        appointment = Appointment(
            appointment_number=apt_num,
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=datetime.now(),
            status='waiting_room', # Reception Check-in Status
            reason=form.notes.data,
            billing=billing # Link billing if model supports it (we checked, it connects via backref 'billing' on Appointment side? No, Appointment has 'billing' backref from Billing model? Billing has 'appointment_id')
        )
        # Wait, Billing has appointment_id. link it after flushing appointment.
        db.session.add(appointment)
        db.session.flush()
        
        billing.appointment_id = appointment.id
        db.session.commit()
        
        flash(f'Patient checked in successfully! Invoice {inv_num} generated.', 'success')
        return redirect(url_for('billing.view', id=billing.id)) # Redirect to pay

    # For initial render (GET) we still want to show the configured fee
    default_fee = Decimal("5.00")
    raw_fee = SystemSetting.get("billing.card_fee", default_fee)
    try:
        card_fee = float(Decimal(str(raw_fee)))
    except Exception:
        card_fee = float(default_fee)

    return render_template('patients/checkin.html', form=form, patient=patient, card_fee=card_fee)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_patients')
def add():
    form = PatientForm()
    if form.validate_on_submit():
        # Calculate date_of_birth from age
        try:
            age_years = int(form.age.data)
            # Approximate DOB as Jan 1 of birth year
            current_year = datetime.now().year
            birth_year = current_year - age_years
            calculated_dob = date(birth_year, 1, 1)
        except (ValueError, TypeError):
            flash('Invalid age provided', 'danger')
            return render_template('patients/create.html', form=form, title="Add New Patient")
        
        patient = Patient(
            patient_id=form.patient_id.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=calculated_dob,
            gender=form.gender.data,
            blood_group=form.blood_group.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            medical_history=form.medical_history.data,
            allergies=form.allergies.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients.index'))
    
    # Auto-generate patient ID if empty
    if not form.patient_id.data:
        last_p = Patient.query.order_by(Patient.id.desc()).first()
        next_id = 1 if not last_p else last_p.id + 1
        form.patient_id.data = f"PAT-{next_id:04d}"

    return render_template('patients/create.html', form=form, title="Add New Patient")

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_patients')
def edit(id):
    patient = Patient.query.get_or_404(id)
    form = PatientForm()
    
    if request.method == 'GET':
        # Pre-populate form with patient data
        form.patient_id.data = patient.patient_id
        form.first_name.data = patient.first_name
        form.last_name.data = patient.last_name
        form.age.data = str(patient.age) if patient.age else ''
        form.gender.data = patient.gender
        form.blood_group.data = patient.blood_group
        form.phone.data = patient.phone
        form.email.data = patient.email
        form.address.data = patient.address
        form.emergency_contact_name.data = patient.emergency_contact_name
        form.emergency_contact_phone.data = patient.emergency_contact_phone
        form.medical_history.data = patient.medical_history
        form.allergies.data = patient.allergies
    
    if form.validate_on_submit():
        # Calculate new DOB from age
        try:
            age_years = int(form.age.data)
            current_year = datetime.now().year
            birth_year = current_year - age_years
            calculated_dob = date(birth_year, 1, 1)
        except (ValueError, TypeError):
            flash('Invalid age provided', 'danger')
            return render_template('patients/create.html', form=form, title="Edit Patient")
        
        patient.patient_id = form.patient_id.data
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.date_of_birth = calculated_dob
        patient.gender = form.gender.data
        patient.blood_group = form.blood_group.data
        patient.phone = form.phone.data
        patient.email = form.email.data
        patient.address = form.address.data
        patient.emergency_contact_name = form.emergency_contact_name.data
        patient.emergency_contact_phone = form.emergency_contact_phone.data
        patient.medical_history = form.medical_history.data
        patient.allergies = form.allergies.data
        
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients.index'))
        
    return render_template('patients/create.html', form=form, title="Edit Patient")

@bp.route('/view/<int:id>')
@login_required
@permission_required('view_patients')
def view(id):
    patient = Patient.query.get_or_404(id)
    return render_template('patients/view.html', patient=patient)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('delete_patients')
def delete(id):
    patient = Patient.query.get_or_404(id)
    patient.soft_delete()
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients.index'))

@bp.route('/statement/<int:id>')
@login_required
@permission_required('view_patients')
def statement(id):
    patient = Patient.query.get_or_404(id)
    
    # Ledger Construction
    transactions = []
    
    billings = Billing.query.filter_by(patient_id=id).order_by(Billing.created_at.asc()).all()
    
    running_balance = 0.0
    
    for bill in billings:
        # 1. Verification of Debt (Invoice)
        # Assuming created_at is the invoice date
        transactions.append({
            'date': bill.created_at,
            'ref': bill.invoice_number,
            'particulars': f"Invoice Generated - #{bill.invoice_number}",
            'type': 'debit',
            'amount': bill.total_amount,
            'd_amt': bill.total_amount,
            'c_amt': 0.0
        })
        
        # 2. Payment (Credit)
        # If paid or partially paid, record the payment
        if bill.paid_amount > 0:
            # If we don't have separate payment dates, we use updated_at or created_at
            pay_date = bill.updated_at if bill.updated_at else bill.created_at
            # Make sure payment appears AFTER invoice if times are identical
            
            transactions.append({
                'date': pay_date,
                'ref': f"PAY-{bill.id}",
                'particulars': f"Payment Received - {bill.payment_method or 'Cash'}",
                'type': 'credit',
                'amount': bill.paid_amount,
                'd_amt': 0.0,
                'c_amt': bill.paid_amount
            })

    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    # Calculate Running Balance
    for t in transactions:
        if t['type'] == 'debit':
            running_balance += float(t['amount'])
        else:
            running_balance -= float(t['amount'])
        t['balance'] = running_balance
        
    return render_template('patients/statement.html', patient=patient, transactions=transactions, now=datetime.now())
