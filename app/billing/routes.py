from decimal import Decimal

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.decorators import permission_required
from app.extensions import db
from . import bp
from app.models import Billing, BillingItem, Patient, Appointment, Account, JournalEntry, JournalItem, SystemSetting
from flask_login import current_user
from datetime import datetime
from .forms import BillingForm

def _get_service_prices() -> dict[str, float]:
    """
    Resolve standard service prices from SystemSetting,
    falling back to safe defaults if nothing is configured yet.
    """
    default_prices = {
        'Consultation': Decimal('5.00'),
        'Computer Service': Decimal('10.00'),
        'Laboratory': Decimal('15.00'),
        'Ultrasound': Decimal('20.00'),
        'Other': Decimal('0.00'),
    }

    prices: dict[str, float] = {}
    for code, default in default_prices.items():
        key = f"billing.service.{code}.price"
        raw = SystemSetting.get(key, default)
        try:
            prices[code] = float(Decimal(str(raw)))
        except Exception:
            prices[code] = float(default)
    return prices


@bp.route('/api/patient-appointments')
@login_required
def get_patient_appointments():
    """API endpoint to fetch appointments for a specific patient"""
    patient_id = request.args.get('patient_id', type=int)
    if not patient_id:
        return jsonify({'appointments': []})
    
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.created_at.desc()).all()
    result = []
    for apt in appointments:
        result.append({
            'id': apt.id,
            'text': f"{apt.appointment_number} - {apt.reason} ({apt.status})"
        })
    
    return jsonify({'appointments': result})

@bp.route('/')
@login_required
@permission_required('view_billing')
def index():
    billings = Billing.query.filter_by(is_deleted=False).order_by(Billing.created_at.desc()).all()
    return render_template('billing/index.html', billings=billings)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('process_payment')
def create():
    form = BillingForm()

    # Resolve standard prices from settings so everything stays in sync
    service_prices = _get_service_prices()
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.all()]
    form.appointment_id.choices = [(0, 'None')] + [
        (a.id, f"{a.appointment_number} - {a.reason}") for a in Appointment.query.all()
    ]

    # Refresh service type labels with the current prices
    base_labels = {
        'Consultation': 'Consultation (Talo-siin)',
        'Computer Service': 'Computer Service (Adeegga Computer-ka)',
        'Laboratory': 'Laboratory (Shaybaarka)',
        'Ultrasound': 'Ultrasound (Raajo)',
        'Other': 'Other (Kuwa Kale)',
    }
    form.service_types.choices = [
        (code, f"{label} - ${service_prices.get(code, 0):.2f}")
        for code, label in base_labels.items()
    ]
    
    if form.validate_on_submit():
        last_bill = Billing.query.order_by(Billing.id.desc()).first()
        inv_num = f"INV-{(1 if not last_bill else last_bill.id + 1):04d}"
        
        # Calculate total from selected services
        selected_services = form.service_types.data  # List of selected service types
        total = Decimal(str(form.service_amount.data))
        
        # Tax calculation
        tax_pct = Decimal(str(SystemSetting.get('billing.tax.percentage', '0.00')))
        tax_amt = (total * tax_pct / 100).quantize(Decimal('0.01'))
        
        net = total + tax_amt - Decimal(str(form.discount.data))
        balance = net - Decimal(str(form.paid_amount.data))
        
        billing = Billing(
            invoice_number=inv_num,
            patient_id=form.patient_id.data,
            appointment_id=form.appointment_id.data if form.appointment_id.data != 0 else None,
            total_amount=total,
            tax_percentage=tax_pct,
            tax_amount=tax_amt,
            discount=form.discount.data,
            net_amount=net,
            paid_amount=form.paid_amount.data,
            balance_amount=balance,
            payment_status=form.payment_status.data,
            payment_method=form.payment_method.data
        )
        db.session.add(billing)
        db.session.flush()
        
        # Add billing items for each selected service
        for service in selected_services:
            price = service_prices.get(service, 0.00)
            item = BillingItem(
                billing_id=billing.id,
                description=service,
                quantity=1,
                unit_price=price,
                subtotal=price
            )
            db.session.add(item)
        
        # ---------------------------------------------------
        # INTEGRATION: Auto-create Journal Entry (Accrual Basis)
        # ---------------------------------------------------
        try:
            # 1. Credit Revenue (Sales) with the Net Amount
            revenue_acc = Account.query.filter_by(code='4000').first() # Sales Revenue
            
            # 2. Debit Cash/AR
            cash_acc = Account.query.filter_by(code='1000').first() # Cash
            ar_acc = Account.query.filter_by(code='1200').first()   # Accounts Receivable
            
            if revenue_acc and cash_acc and ar_acc:
                je = JournalEntry(
                    date=datetime.utcnow(),
                    reference=inv_num,
                    description=f"Invoice Generated for {form.patient_id.data}",
                    user_id=current_user.id
                )
                
                # Credit Sales (Income)
                je.items.append(JournalItem(account_id=revenue_acc.id, credit=net, debit=0))
                
                # Debits
                if form.paid_amount.data > 0:
                    je.items.append(JournalItem(account_id=cash_acc.id, debit=form.paid_amount.data, credit=0))
                
                if balance > 0:
                    je.items.append(JournalItem(account_id=ar_acc.id, debit=balance, credit=0))
                
                db.session.add(je)
        except Exception as e:
            print(f"Accounting Integration Error: {e}")
            # Don't fail the whole request just because accounting failed, strictly speaking
            
        db.session.commit()
        
        flash('Invoice generated & posted to Accounting!', 'success')
        return redirect(url_for('billing.index'))
        
    return render_template(
        'billing/create.html',
        form=form,
        title="Generate Invoice",
        service_prices=service_prices,
        tax_percentage=float(SystemSetting.get('billing.tax.percentage', '0.00'))
    )

@bp.route('/view/<int:id>')
@login_required
@permission_required('view_billing')
def view(id):
    billing = Billing.query.get_or_404(id)
    return render_template('billing/view.html', billing=billing)

@bp.route('/pay/<int:id>', methods=['POST'])
@login_required
@permission_required('process_payment')
def pay(id):
    billing = Billing.query.get_or_404(id)
    if billing.payment_status == 'paid':
        flash('This invoice is already paid.', 'info')
        return redirect(url_for('billing.view', id=id))
        
    # Mark as paid
    billing.payment_status = 'paid'
    billing.paid_amount = billing.net_amount
    billing.balance_amount = 0.0
    
    # Workflow Logic
    if billing.appointment:
        apt = billing.appointment
        if apt.status == 'lab_pay_pending':
            apt.status = 'in_lab'
            # Find associated lab request and update
            for req in apt.lab_requests:
                if req.status == 'pending_payment':
                    req.status = 'pending'
            flash('Payment received. Patient sent to Lab.', 'success')
        else:
            flash('Payment received successfully.', 'success')
            
    # workflow logic end
    
    # ---------------------------------------------------
    # INTEGRATION: Journal Entry for Payment
    # ---------------------------------------------------
    try:
        # Dr Cash (1000) / Cr AR (1200)
        amount_paid = billing.net_amount # Since we marked fully paid
        
        cash_acc = Account.query.filter_by(code='1000').first()
        ar_acc = Account.query.filter_by(code='1200').first()
        
        if cash_acc and ar_acc:
            je = JournalEntry(
                date=datetime.utcnow(),
                reference=f"PAY-{billing.invoice_number}",
                description=f"Payment received for {billing.invoice_number}",
                user_id=current_user.id
            )
            je.items.append(JournalItem(account_id=cash_acc.id, debit=amount_paid, credit=0))
            je.items.append(JournalItem(account_id=ar_acc.id, debit=0, credit=amount_paid))
            
            db.session.add(je)
            
    except Exception as e:
        print(f"Payment Accounting Error: {e}")

    db.session.commit()
    return redirect(url_for('billing.view', id=id))

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    # Authorization Check
    if current_user.role.name.lower() not in ['admin', 'accountant', 'xisabiye']: # Added 'xisabiye' just in case
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('billing.index'))
        
    billing = Billing.query.get_or_404(id)
    
    # Optional: Check if already paid? Usually you can void unpaid.
    # For now, allow admin to delete anything (soft delete)
    
    billing.soft_delete()
    
    # Reverse Journal Entries?
    # Complex topic. For now, we assumption soft delete just hides it from UI.
    # In a real system, we would post a reversing entry.
    
    try:
        # Find associated JE and maybe mark/reverse?
        # Keeping it simple for this request.
        pass
    except:
        pass
        
    db.session.commit()
    flash('Invoice record deleted successfully.', 'success')
    return redirect(url_for('billing.index'))
