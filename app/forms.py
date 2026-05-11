from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired, DataRequired, Optional
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.fields import DateTimeLocalField

# Reusable choices 
ITEM_CATEGORIES = [
    ('bags_backpacks', 'Bags & Backpacks'),
    ('bottles_flasks', 'Bottles & Flasks'),
    ('clothing', 'Clothing'),
    ('computers_electronics', 'Computers & Electronics'),
    ('eyewear', 'Eyewear'),
    ('footwear', 'Footwear'),
    ('ids_cards', 'IDs & Cards'),
    ('keys', 'Keys'),
    ('mobile_devices', 'Mobile Devices'),
    ('wallets_purses', 'Wallets & Purses'),
    ('watches_jewelry', 'Watches & Jewelry'),
    ('misc', 'Miscellaneous')
]

class LoginForm(FlaskForm):
    userID = StringField('userID', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class LostItemReportForm(FlaskForm): 
    category = SelectField('Item Category', choices=ITEM_CATEGORIES)
    date_lost = DateTimeLocalField('Date and Time Lost', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    phone_number = StringField('Phone', validators=[InputRequired()])
    description = TextAreaField('Description', validators=[InputRequired()]) 
    photo = FileField('Photo (Optional)', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])

class FoundItemReportForm(FlaskForm):
    category = SelectField('Item Category', choices=ITEM_CATEGORIES)
    
 
    date_found = DateTimeLocalField('Date and Time Found', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    phone_number = StringField('Your Phone/Office Phone', validators=[InputRequired()])
    
    office_name = StringField('Office Name', validators=[Optional()])
    office_directions = TextAreaField('Office Directions', validators=[Optional()])

    # If the admin has a photo, it's better for the AI!
    photo = FileField('Photo', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    description = TextAreaField('Description', validators=[Optional()])