from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed


class LoginForm(FlaskForm):
    userID = StringField('userID', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

#LOST AND FOUND REPORT FORMS 