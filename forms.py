from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

class LoginForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  password = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
  submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  password = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

class PermissionForm(FlaskForm):
  is_admin = BooleanField('Is Admin')
  can_print = BooleanField('Can Print')
  can_upload = BooleanField('Can Upload')
  can_view = BooleanField('Can View')
  can_delete = BooleanField('Can Delete')
  can_stop = BooleanField('Can Stop')
  submit = SubmitField('Update Permissions')

class UploadForm(FlaskForm):
  submit = SubmitField('Upload file')
