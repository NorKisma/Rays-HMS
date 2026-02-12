from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField ,SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# -------------------------
# LOGIN FORM
# -------------------------



class EditUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    role_id = SelectField("Role", coerce=int)
    is_active = BooleanField("Active")
    password_hash = PasswordField("New Password")  # <-- maybe this is what you called it
    submit = SubmitField("Update")




class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

# -------------------------
# REGISTER FORM (Public)
# -------------------------
class RegisterForm(FlaskForm):
    name = StringField(
        'Full Name', 
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password')]
    )

    # Must match route requirement
    role_id = SelectField(
        "Role",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Register")


   
# -------------------------
# CHANGE PASSWORD FORM
# -------------------------
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )
    submit = SubmitField("Update Password")

from wtforms import SelectMultipleField, widgets

class RoleForm(FlaskForm):
    name = StringField("Role Name", validators=[DataRequired(), Length(max=50)])
    description = StringField("Description", validators=[Length(max=255)])
    permissions = SelectMultipleField(
        "Permissions", 
        coerce=int,
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )
    submit = SubmitField("Save Role")