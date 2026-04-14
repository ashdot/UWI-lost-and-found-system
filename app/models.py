from flask_login import UserMixin
from .extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin,db.Model):

    __tablename__ = 'User'
    
    userID = db.Column(db.Integer, primary_key=True)

    firstName = db.Column(db.String(80))
    lastName = db.Column(db.String(80))

    email = db.Column(db.String(100))
    password = db.Column(db.String(255))

    # Updated Role Column
    role = db.Column(db.String(20), nullable=False)

    # This ensures ONLY these three strings can ever be saved in Postgres
    __table_args__ = (
        CheckConstraint(role.in_(['student', 'staff', 'admin']), name='role_types'),
    )


    #failed_attempted = db.Column(db.Integer, default=0) #Causing issues so commented out 

    #lock_until = db.Column(db.DateTime(timezone=True), nullable=True) #Causing issues so commented out 

    def __init__(self, userID=None, firstName=None, lastName=None, email=None, role=None, password=None):
        if userID:
            self.userID = userID

        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.role = role

        if password:
            self.password = generate_password_hash(password, method='pbkdf2:sha256')

    
    def get_id(self):
        return str(self.userID)

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
    #location_lost = db.Column(db.String(100))

    userID = db.Column(db.Integer, db.ForeignKey('User.userID'))

    description = db.relationship('LostItemDescription', backref='report', uselist=False)


#Picture should be optional here 
class FoundItemReport(db.Model):
    __tablename__ = 'found_item_report'

    reportID = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(10))

    date_found = db.Column(db.DateTime)
    #location_found = db.Column(db.String(100))

    office_name = db.Column(db.String(100))

    adminID = db.Column(db.Integer, db.ForeignKey('User.userID'))

    #office_location = db.Column(db.String(100)) #Should Probably delete this 

    office_directions = db.Column(db.String(255))

    description = db.relationship('FoundItemDescription', backref='report', uselist=False)


class LostItemDescription(db.Model):
    __tablename__ = 'lost_item_description'

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50))
    text_description = db.Column(db.Text)
    
    # Text AI Numbers
    text_embedding = db.Column(db.PickleType)
    # ADD THIS: Image AI Numbers
    image_embedding = db.Column(db.PickleType, nullable=True) 

    photo_url = db.Column(db.String(255), nullable=True)
    report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'))


class FoundItemDescription(db.Model):
    __tablename__ = 'found_item_description'

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50))
    text_description = db.Column(db.Text, nullable=True)
    
    # Text AI Numbers
    text_embedding = db.Column(db.PickleType, nullable=True)
    # ADD THIS: Image AI Numbers
    image_embedding = db.Column(db.PickleType, nullable=True) 
    
    photo_url = db.Column(db.String(255), nullable=True)
    report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'))


class Match(db.Model):
    __tablename__ = 'match'

    matchID = db.Column(db.Integer, primary_key=True)
    
    lost_report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'), nullable=False)
    found_report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'), nullable=False)

    similarity_score = db.Column(db.Float, nullable=False) 
    
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships to access data easily
    lost_report = db.relationship('LostItemReport', backref='matches_as_lost')
    found_report = db.relationship('FoundItemReport', backref='matches_as_found')