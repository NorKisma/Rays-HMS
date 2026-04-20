import os
from decimal import Decimal, InvalidOperation

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.decorators import admin_required
from app.extensions import db
from app.models import SystemSetting
from app.models.lab import LabTest

from . import bp
from .forms import BillingSettingsForm


def _get_decimal_setting(key: str, default: Decimal) -> Decimal:
    raw = SystemSetting.get(key)
    if raw is None:
        return default
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return default


@bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def index():
    # Defaults
    default_prices = {
        "Consultation": Decimal("5.00"),
        "Computer Service": Decimal("10.00"),
        "Laboratory": Decimal("15.00"),
        "Ultrasound": Decimal("20.00"),
        "Other": Decimal("0.00"),
    }
    default_card_fee = Decimal("5.00")

    # Load current values
    current_prices = {}
    for code, default_value in default_prices.items():
        key = f"billing.service.{code}.price"
        current_prices[code] = _get_decimal_setting(key, default_value)

    card_fee = _get_decimal_setting("billing.card_fee", default_card_fee)
    lab_tests = LabTest.query.all()

    form = BillingSettingsForm()

    if request.method == "GET":
        form.consultation_price.data = current_prices["Consultation"]
        form.computer_service_price.data = current_prices["Computer Service"]
        form.laboratory_price.data = current_prices["Laboratory"]
        form.ultrasound_price.data = current_prices["Ultrasound"]
        form.other_service_price.data = current_prices["Other"]
        form.card_fee.data = card_fee

    if form.validate_on_submit():
        # 1. Update standard settings
        SystemSetting.set("billing.service.Consultation.price", form.consultation_price.data, group="billing")
        SystemSetting.set("billing.service.Computer Service.price", form.computer_service_price.data, group="billing")
        SystemSetting.set("billing.service.Laboratory.price", form.laboratory_price.data, group="billing")
        SystemSetting.set("billing.service.Ultrasound.price", form.ultrasound_price.data, group="billing")
        SystemSetting.set("billing.service.Other.price", form.other_service_price.data, group="billing")
        SystemSetting.set("billing.card_fee", form.card_fee.data, group="billing")

        # 2. Check for manual new lab test addition
        new_test_name = request.form.get('new_lab_test_name')
        new_test_price = request.form.get('new_lab_test_price')
        if new_test_name and new_test_price:
            try:
                nt = LabTest(name=new_test_name, price=Decimal(new_test_price))
                db.session.add(nt)
            except (InvalidOperation, TypeError):
                flash("Invalid lab test price", "danger")

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("settings.index"))

    return render_template(
        "settings/index.html",
        form=form,
        current_prices=current_prices,
        card_fee=card_fee,
        lab_tests=lab_tests
    )

@bp.route("/profile", methods=["POST"])
@login_required
@admin_required
def update_profile():
    if not current_user.hospital:
        flash("Hospital record not found.", "danger")
        return redirect(url_for("settings.index"))

    hospital = current_user.hospital
    hospital.name = request.form.get("hospital_name")
    hospital.phone = request.form.get("hospital_phone")
    hospital.email = request.form.get("hospital_email")
    hospital.website = request.form.get("hospital_website")
    hospital.address = request.form.get("hospital_address")
    
    # Handle Logo Upload
    if 'hospital_logo' in request.files:
        file = request.files['hospital_logo']
        if file and file.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join('app', 'static', 'uploads', 'logos')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file with unique name
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"logo_{hospital.id}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Update hospital logo path
            hospital.logo = f"uploads/logos/{filename}"

    db.session.commit()
    flash("Hospital profile updated successfully.", "success")
    return redirect(url_for("settings.index"))

@bp.route("/lab-test/delete/<int:id>")
@login_required
@admin_required
def delete_lab_test(id):
    test = LabTest.query.get_or_404(id)
    db.session.delete(test)
    db.session.commit()
    flash(f"Test '{test.name}' removed.", "info")
    return redirect(url_for("settings.index"))
