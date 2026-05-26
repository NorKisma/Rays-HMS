from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, BooleanField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class VisitorLogForm(FlaskForm):
    visitor_name = StringField('Visitor Name', validators=[DataRequired(), Length(max=150)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=25)])
    purpose = SelectField('Purpose of Visit', choices=[
        ('Visiting Patient', 'Visiting Patient'),
        ('Supplier', 'Supplier/Vendor'),
        ('Official Business', 'Official Business'),
        ('Job Interview', 'Job Interview'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    id_type = SelectField('ID Type Verified', choices=[
        ('', 'No ID Verified'),
        ('National ID', 'National ID'),
        ('Passport', 'Passport'),
        ('Driver\'s License', 'Driver\'s License'),
        ('Work ID', 'Work ID')
    ], validators=[Optional()])
    id_number = StringField('ID Number', validators=[Optional(), Length(max=50)])
    patient_id = SelectField('Link to Patient', coerce=int, validators=[Optional()])
    temperature = StringField('Temperature (°C)', validators=[Optional(), Length(max=10)], default='36.5')
    symptoms = TextAreaField('Symptoms / Health Screening Notes', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Log Visitor Check-In')

class CallLogForm(FlaskForm):
    caller_name = StringField('Caller Name', validators=[DataRequired(), Length(max=150)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=25)])
    call_type = SelectField('Call Type', choices=[
        ('Incoming', 'Incoming'),
        ('Outgoing', 'Outgoing')
    ], validators=[DataRequired()])
    call_category = SelectField('Call Category', choices=[
        ('Appointment Booking', 'Appointment Booking'),
        ('General Inquiry', 'General Inquiry'),
        ('Emergency', 'Emergency'),
        ('Billing Dispute', 'Billing Dispute'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    details = TextAreaField('Call Details / Request', validators=[DataRequired()])
    action_taken = TextAreaField('Action Taken', validators=[Optional()])
    follow_up_required = BooleanField('Follow-up Required')
    follow_up_date = DateTimeField('Follow-up Date & Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Log Call')
