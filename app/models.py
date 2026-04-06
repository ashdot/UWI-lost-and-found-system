from flask_login import UserMixin
from .extensions import db
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin,db.Model):

    __tablename__ = 'User'
    
    userID = db.Column(db.Integer, primary_key=True)

    firstName = db.Column(db.String(80))
    lastName = db.Column(db.String(80))

    email = db.Column(db.String(100))
    password = db.Column(db.String(128))

    role = db.Column(db.String(50))


    failed_attempted = db.Column(db.Integer, default=0)

    lock_until = db.Column(db.DateTime(timezone=True), nullable=True)

    def __init__(self, userID=None, firstName=None, lastName=None, role=None, password=None):
        if userID:
            self.userID = userID
        self.firstName = firstName
        self.lastName = lastName
        self.role = role
        if password:
            self.password = generate_password_hash(password, method='pbkdf2:sha256')



    #PASSWORD METHODS 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        if self.lock_until and datetime.now(timezone.utc) < self.lock_until:
            return True
        return False

    def register_failed_attempt(self):
        self.failed_attempted += 1
        if self.failed_attempted >= 3:
            self.lock_until = datetime.now(timezone.utc) + timedelta(minutes=30)


# TO BE DONE -> LOST AND FOUND REPORT MODELS 

class LostItemReport(db.Model):

    __tablename__ = 'lost_item_report'

    reportID = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(10))

    date_lost = db.Column(db.DateTime)
    location_lost = db.Column(db.String(100))

    description = db.relationship('LostItemDescription', backref='report', uselist=False)


class LostItemDescription(db.Model):

    __tablename__ = 'lost_item_description'

    id = db.Column(db.Integer, primary_key=True)

    item_type = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    color = db.Column(db.String(30))

    text_description = db.Column(db.Text)
    text_embedding = db.Column(db.PickleType)

    report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'))

class FoundItemReport(db.Model):
    __tablename__ = 'found_item_report'

    reportID = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(10))

    date_found = db.Column(db.DateTime)
    location_found = db.Column(db.String(100))


    office_name = db.Column(db.String(100))
    office_location = db.Column(db.String(100))

    description = db.relationship('FoundItemDescription', backref='report', uselist=False)

class FoundItemDescription(db.Model):
    
    __tablename__ = 'found_item_description'

    id = db.Column(db.Integer, primary_key=True)

    item_type = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    color = db.Column(db.String(30))

    text_description = db.Column(db.Text)
    text_embedding = db.Column(db.PickleType)

    report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'))