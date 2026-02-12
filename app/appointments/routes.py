from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.decorators import permission_required
from app.extensions import db
from . import bp
from app.models import Appointment, Patient, Doctor, Billing, BillingItem, LabRequest
from .forms import AppointmentForm, ConsultationForm

@bp.route('/')
@login_required
@permission_required('view_appointments')
def index():
    appointments = Appointment.query.filter_by(is_deleted=False).order_by(Appointment.appointment_date.desc()).all()
    return render_template('appointments/index.html', appointments=appointments)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_appointments')
def add():
    form = AppointmentForm()
    # Dynamic data loading
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name} ({p.patient_id})") for p in Patient.query.filter_by(is_deleted=False).all()]
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name} ({d.specialization})") for d in Doctor.query.filter_by(is_deleted=False).all()]
    
    if form.validate_on_submit():
        last_apt = Appointment.query.order_by(Appointment.id.desc()).first()
        apt_num = f"APT-{(1 if not last_apt else last_apt.id + 1):04d}"
        
        appointment = Appointment(
            appointment_number=apt_num,
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_date=form.appointment_date.data,
            reason=form.reason.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('appointments.index'))
    return render_template('appointments/create.html', form=form, title="Schedule Appointment")

@bp.route('/view/<int:id>')
@login_required
@permission_required('view_appointments')
def view(id):
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointments/view.html', appointment=appointment)

@bp.route('/consult/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('add_diagnosis')
def consult(id):
    appointment = Appointment.query.get_or_404(id)
    form = ConsultationForm(obj=appointment)
    
    if form.validate_on_submit():
        # Update Vitals and Notes
        appointment.vitals_temperature = form.vitals_temperature.data
        appointment.vitals_blood_pressure = form.vitals_blood_pressure.data
        appointment.vitals_weight = form.vitals_weight.data
        appointment.diagnosis = form.diagnosis.data
        appointment.prescription = form.prescription.data
        
        action = form.lab_test_required.data
        
        if action == 'lab':
            # 1. Create Lab Request
            lab_req = LabRequest(
                appointment_id=appointment.id,
                test_name=form.lab_test_description.data,
                description=f"Ordered by Dr. {appointment.doctor.last_name}",
                status='pending_payment'
            )
            db.session.add(lab_req)
            
            # 2. Create Bill for Lab
            # Generate Invoice Number unique (time-based for now)
            import time
            inv_num = f"INV-L-{int(time.time())}"
            lab_fee = 20.00 # Placeholder standard lab fee
            
            billing = Billing(
                invoice_number=inv_num,
                patient_id=appointment.patient_id,
                appointment_id=appointment.id, # Link to this appointment
                total_amount=lab_fee,
                net_amount=lab_fee,
                balance_amount=lab_fee,
                payment_status='unpaid'
            )
            db.session.add(billing)
            db.session.flush()
            
            item = BillingItem(
                billing_id=billing.id,
                description=f"Lab Tests: {form.lab_test_description.data}",
                quantity=1,
                unit_price=lab_fee,
                subtotal=lab_fee
            )
            db.session.add(item)
            
            # 3. Update Status
            appointment.status = 'lab_pay_pending'
            flash('Lab tests ordered. Patient sent to Reception for payment.', 'info')
            
        elif action == 'pharmacy':
            appointment.status = 'in_pharmacy'
            flash('Consultation finished. Patient sent to Pharmacy.', 'success')
            
        else: # none
            appointment.status = 'completed'
            flash('Consultation completed successfully.', 'success')
            
        db.session.commit()
        return redirect(url_for('appointments.index'))
    
    return render_template('appointments/consult.html', form=form, appointment=appointment)

@bp.route('/status/<int:id>/<string:status>')
@login_required
@permission_required('edit_appointments')
def update_status(id, status):
    appointment = Appointment.query.get_or_404(id)
    appointment.status = status
    db.session.commit()
    flash(f'Appointment status updated to {status.replace("_", " ").title()}', 'info')
    return redirect(request.referrer or url_for('appointments.index'))

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('delete_appointments')
def delete(id):
    appointment = Appointment.query.get_or_404(id)
    appointment.soft_delete()
    db.session.commit()
    flash('Appointment deleted successfully!', 'success')
    return redirect(url_for('appointments.index'))
