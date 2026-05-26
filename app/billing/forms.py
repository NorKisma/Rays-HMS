from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, IntegerField, SubmitField, FieldList, FormField, SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Optional, NumberRange

class BillingItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    quantity = IntegerField('Qty', validators=[DataRequired(), NumberRange(min=1)], default=1)
    unit_price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])

class BillingForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    appointment_id = SelectField('Linked Appointment', coerce=int, validators=[Optional()])
    
    service_types = SelectMultipleField('Service Types', choices=[
        ('Consultation', 'Consultation (Talo-siin) - $5.00'), 
        ('Computer Service', 'Computer Service (Adeegga Computer-ka) - $10.00'),
        ('Laboratory', 'Laboratory (Shaybaarka) - $15.00'),
        ('Ultrasound', 'Ultrasound (Raajo) - $20.00'),
        ('Card_General', 'General Card (Kaarka Caadiga ah) - $3.00'),
        ('Card_Specialist', 'Specialist Card (Kaarka Khaska ah) - $10.00'),
        ('Card_Emergency', 'Emergency Card (Kaarka Degdegga ah) - $5.00'),
        ('Other', 'Other (Kuwa Kale)')
    ], widget=ListWidget(prefix_label=False), option_widget=CheckboxInput(), validators=[DataRequired()])
    
    service_amount = DecimalField('Service Cost ($)', default=0.0, validators=[DataRequired()])
    
    discount = DecimalField('Discount Amount', default=0.0)
    payment_method = SelectField('Payment Method', choices=[
        ('Cash', 'Cash'),
        ('Card', 'Debit/Credit Card'),
        ('Insurance', 'Insurance'),
        ('Bank Transfer', 'Bank Transfer')
    ])
    payment_status = SelectField('Status', choices=[
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid')
    ])
    paid_amount = DecimalField('Paid Amount', default=0.0)
    submit = SubmitField('Generate Invoice')
