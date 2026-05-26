from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length

class PatientForm(FlaskForm):
    # (Previous fields stay as they are)
    patient_id = StringField('Patient ID', validators=[DataRequired(), Length(max=20)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    age = StringField('Age (Years)', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', validators=[Optional()], choices=[
        ('', 'Select Blood Group'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional()])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=150)])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    submit = SubmitField('Save Patient')

class CheckInForm(FlaskForm):
    doctor_id = SelectField('Assign to Doctor', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Reception Notes', validators=[Optional()])
    pay_immediately = SelectField('Payment Status', choices=[('yes', 'Collect Cashier Payment Directly (Paid)'), ('no', 'Forward to Cashier Desk (Unpaid)')], default='yes', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[('Cash', 'Cash'), ('EVC Plus', 'EVC Plus'), ('E-Dahab', 'E-Dahab'), ('Zaad', 'Zaad'), ('Bank Transfer', 'Bank Transfer')], default='Cash')
    submit = SubmitField('Check In & Create Invoice')
