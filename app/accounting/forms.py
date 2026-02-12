
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, DateField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

class AccountForm(FlaskForm):
    code = StringField('Account Code', validators=[DataRequired(), Length(max=20)])
    name = StringField('Account Name', validators=[DataRequired(), Length(max=100)])
    type = SelectField('Account Type', choices=[
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Revenue', 'Revenue'),
        ('Expense', 'Expense')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=255)])

class JournalItemForm(FlaskForm):
    account_id = SelectField('Account', coerce=int, validators=[DataRequired()])
    debit = DecimalField('Debit', validators=[Optional()], default=0.0)
    credit = DecimalField('Credit', validators=[Optional()], default=0.0)
    description = StringField('Line Desc', validators=[Optional()])

# Note: Complex dynamic forms often require JS handling, 
# but we can leave the structure here or handle raw form data in the route.
class JournalEntryForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    reference = StringField('Reference', validators=[Optional(), Length(max=100)])
    description = StringField('Narration', validators=[DataRequired(), Length(max=255)])
