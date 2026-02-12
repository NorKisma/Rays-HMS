from decimal import Decimal, InvalidOperation

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.decorators import admin_required
from app.extensions import db
from app.models import SystemSetting

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
    """
    Central settings screen.

    First version focuses on:
    - Billing service prices (consultation, lab, etc.)
    - Reception card/registration fee
    """
    # Defaults that mirror current hard-coded behaviour
    default_prices = {
        "Consultation": Decimal("5.00"),
        "Computer Service": Decimal("10.00"),
        "Laboratory": Decimal("15.00"),
        "Ultrasound": Decimal("20.00"),
        "Other": Decimal("0.00"),
    }
    default_card_fee = Decimal("5.00")

    # Load current values from DB (or defaults)
    current_prices: dict[str, Decimal] = {}
    for code, default_value in default_prices.items():
        key = f"billing.service.{code}.price"
        current_prices[code] = _get_decimal_setting(key, default_value)

    card_fee = _get_decimal_setting("billing.card_fee", default_card_fee)

    form = BillingSettingsForm()

    # Pre-fill form on GET
    if request.method == "GET":
        form.consultation_price.data = current_prices["Consultation"]
        form.computer_service_price.data = current_prices["Computer Service"]
        form.laboratory_price.data = current_prices["Laboratory"]
        form.ultrasound_price.data = current_prices["Ultrasound"]
        form.other_service_price.data = current_prices["Other"]
        form.card_fee.data = card_fee

    if form.validate_on_submit():
        # Persist settings
        SystemSetting.set(
            "billing.service.Consultation.price",
            form.consultation_price.data,
            group="billing",
            description="Standard price for Consultation service",
        )
        SystemSetting.set(
            "billing.service.Computer Service.price",
            form.computer_service_price.data,
            group="billing",
            description="Standard price for Computer Service",
        )
        SystemSetting.set(
            "billing.service.Laboratory.price",
            form.laboratory_price.data,
            group="billing",
            description="Standard price for Laboratory service",
        )
        SystemSetting.set(
            "billing.service.Ultrasound.price",
            form.ultrasound_price.data,
            group="billing",
            description="Standard price for Ultrasound service",
        )
        SystemSetting.set(
            "billing.service.Other.price",
            form.other_service_price.data,
            group="billing",
            description="Default price for Other services (if any)",
        )
        SystemSetting.set(
            "billing.card_fee",
            form.card_fee.data,
            group="billing",
            description="Reception card / registration fee used at check-in",
        )

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("settings.index"))

    return render_template(
        "settings/index.html",
        form=form,
        current_prices=current_prices,
        card_fee=card_fee,
    )

