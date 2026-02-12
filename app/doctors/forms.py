from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange

class DoctorForm(FlaskForm):
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    specialization = SelectField('Specialization', choices=[
        ('', 'Select Specialization'),
        ('General Physician', 'General Physician'),
        ('Cardiology', 'Cardiology'),
        ('Dermatology', 'Dermatology'),
        ('Neurology', 'Neurology'),
        ('Pediatrics', 'Pediatrics'),
        ('Orthopedics', 'Orthopedics'),
        ('Psychiatry', 'Psychiatry'),
        ('Gynecology', 'Gynecology'),
        ('Surgery', 'Surgery')
    ], validators=[DataRequired()])
    qualification = StringField('Qualification', validators=[Optional(), Length(max=255)])
    experience_years = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    consultation_fee = DecimalField('Consultation Fee', validators=[Optional()])
    availability_status = SelectField('Availability', choices=[
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('on_leave', 'On Leave')
    ], default='available')
    submit = SubmitField('Save Doctor')
