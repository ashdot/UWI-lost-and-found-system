from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,FileField,TextAreaField,SelectField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed


class LoginForm(FlaskForm):
    userID = StringField('userID', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

#LOST AND FOUND REPORT FORMS 

#Gets the details from the person who Lost the Item, this should be attatched to a report ID 
class LostItemReportForm(FlaskForm): 

    #Ask group members tmr what catergory this should be 
    #catergory = SelectField 

    phone_number = StringField('Phone', validators=[InputRequired()])
    name = StringField('Name', validators=[InputRequired()])
    description = TextAreaField('Description',validators=[InputRequired()] ) 

    #This Field should be optional 
    photo = FileField('File', validators=[FileRequired(),FileAllowed(['jpg', 'png'], 'Images only!')])


class FoundItemReportForm(FlaskForm):

    #Ask group members tmr what catergory this should be 
    #catergory = SelectField


    photo = FileField('File', validators=[FileRequired(),FileAllowed(['jpg', 'png'], 'Images only!')])

    #This Field should be optional 
    description = TextAreaField('Description',validators=[InputRequired()] ) 

