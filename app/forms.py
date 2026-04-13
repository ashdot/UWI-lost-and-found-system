from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,FileField,TextAreaField,SelectField, SubmitField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import Optional

class LoginForm(FlaskForm):
    userID = StringField('userID', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

#LOST AND FOUND REPORT FORMS 

#Gets the details from the person who Lost the Item, this should be attatched to a report ID 
class LostItemReportForm(FlaskForm): 

    category = SelectField(
    'Item Category',
    choices=[
        ('bags_backpacks', 'Bags & Backpacks'),
        ('clothing', 'Clothing'),
        ('computers_electronics', 'Computers & Electronics'),
        ('eyewear', 'Eyewear'),
        ('footwear', 'Footwear'),
        ('ids_cards', 'IDs & Cards'),
        ('keys', 'Keys'),
        ('misc', 'Miscellaneous'),
        ('mobile_devices', 'Mobile Devices'),
        ('transport_devices', 'Transportation Devices'),
        ('wallets_purses', 'Wallets & Purses'),
        ('watches_jewelry', 'Watches & Jewelry')
    ])

    phone_number = StringField('Phone', validators=[InputRequired()])

    name = StringField('Name', validators=[InputRequired()])

    description = TextAreaField('Description',validators=[InputRequired()] ) 

    #This Field should be optional 
    photo = FileField('Photo', validators=[Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])


class FoundItemReportForm(FlaskForm):

    
    category = SelectField(
    'Item Category',
    choices=[
        ('bags_backpacks', 'Bags & Backpacks'),
        ('clothing', 'Clothing'),
        ('computers_electronics', 'Computers & Electronics'),
        ('eyewear', 'Eyewear'),
        ('footwear', 'Footwear'),
        ('ids_cards', 'IDs & Cards'),
        ('keys', 'Keys'),
        ('misc', 'Miscellaneous'),
        ('mobile_devices', 'Mobile Devices'),
        ('transport_devices', 'Transportation Devices'),
        ('wallets_purses', 'Wallets & Purses'),
        ('watches_jewelry', 'Watches & Jewelry')
    ])


    photo = FileField('File', validators=[FileRequired(),FileAllowed(['jpg', 'png'], 'Images only!')])

    #This Field should be optional 
    description = TextAreaField('Description', validators=[Optional()])

