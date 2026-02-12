from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeLocalField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class AppointmentForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_date = DateTimeLocalField('Appointment Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    reason = StringField('Reason for Visit', validators=[Optional(), Length(max=255)])
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('arrived', 'Arrived'),
        ('in_consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')
    notes = TextAreaField('Administrative Notes', validators=[Optional()])
    submit = SubmitField('Schedule Appointment')

class ConsultationForm(FlaskForm):
    vitals_temperature = StringField('Temperature (°C)', validators=[Optional()])
    vitals_blood_pressure = StringField('Blood Pressure (mmHg)', validators=[Optional()])
    vitals_weight = StringField('Weight (kg)', validators=[Optional()])
    diagnosis = TextAreaField('Diagnosis', validators=[Optional()])
    
    # Lab Request Fields
    lab_test_required = SelectField('Action Needed', choices=[
        ('none', 'None (Complete Consultation)'),
        ('lab', 'Order Lab Test'),
        ('pharmacy', 'Prescribe & Send to Pharmacy')
    ], default='none')
    lab_test_description = TextAreaField('Lab Tests Required', validators=[Optional()], description="List required tests if ordering lab work")
    
    prescription = TextAreaField('Prescription', validators=[Optional()])
    
    submit = SubmitField('Update Consultation Data')
