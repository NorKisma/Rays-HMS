from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FieldList, FormField, FloatField
from wtforms.validators import DataRequired, Optional

class VitalForm(FlaskForm):
    weight = StringField('Weight (kg)', validators=[Optional()])
    height = StringField('Height (cm)', validators=[Optional()])
    temperature = StringField('Temperature (°C)', validators=[Optional()])
    blood_pressure = StringField('Blood Pressure (mmHg)', validators=[Optional()])
    heart_rate = StringField('Heart Rate (bpm)', validators=[Optional()])
    respiratory_rate = StringField('Respiratory Rate (bpm)', validators=[Optional()])
    spo2 = StringField('SpO2 (%)', validators=[Optional()])
    note = TextAreaField('Nursing Notes', validators=[Optional()])
    submit = SubmitField('Record Vitals')

class PrescriptionItemForm(FlaskForm):
    medicine_name = StringField('Medicine Name', validators=[DataRequired()])
    dosage = StringField('Dosage (e.g. 500mg)', validators=[Optional()])
    frequency = StringField('Frequency (e.g. 1x3)', validators=[Optional()])
    duration = StringField('Duration (e.g. 7 days)', validators=[DataRequired()])
    instructions = StringField('Instructions', validators=[Optional()])

class PrescriptionForm(FlaskForm):
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_id = SelectField('Appointment (Optional)', coerce=int, validators=[Optional()])
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    notes = TextAreaField('Clinical Notes', validators=[Optional()])
    submit = SubmitField('Create Prescription')
