from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import Required


class SignupForm(Form):
    username = StringField('Username', validators=[Required()])
    password = StringField('Enter password : ', validators=[Required()])
    submit = SubmitField('Complete registration and back to home')

class LoginForm(Form):
    """Accepts a nickname and a room."""
    username = StringField('Username', validators=[Required()])
    password = StringField('Enter password : ', validators=[Required()])
    submit = SubmitField('Log me in')


class ConnectToForm(Form):
    """Accepts a nickname and a room."""
    connectto = StringField('Who do you want to message : ', validators=[Required()])
    submit = SubmitField('Connect me')
