from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class LabResultForm(FlaskForm):
    result = TextAreaField('Test Results', validators=[DataRequired()])
    submit = SubmitField('Submit Results')
