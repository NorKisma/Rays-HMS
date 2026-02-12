from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class BillingSettingsForm(FlaskForm):
    """Configure standard service prices and card/registration fee."""

    consultation_price = DecimalField(
        "Consultation Price ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("5.00"),
    )
    computer_service_price = DecimalField(
        "Computer Service Price ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("10.00"),
    )
    laboratory_price = DecimalField(
        "Laboratory Price ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("15.00"),
    )
    ultrasound_price = DecimalField(
        "Ultrasound Price ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("20.00"),
    )
    other_service_price = DecimalField(
        "Other Service Default Price ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("0.00"),
    )

    card_fee = DecimalField(
        "Reception Card / Registration Fee ($)",
        validators=[DataRequired(), NumberRange(min=0)],
        default=Decimal("5.00"),
    )

    submit = SubmitField("Save Settings")

