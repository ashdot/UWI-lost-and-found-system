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

    email = db.Column(db.String(100), unique=True) # Make this unique 
    password = db.Column(db.String(255))

    role = db.Column(db.String(20), nullable=False)

    # This ensures ONLY these three strings can ever be saved in Postgres
    __table_args__ = (
        CheckConstraint(role.in_(['student', 'staff', 'admin']), name='role_types'),

        # Add a composite index for name searches
        db.Index('idx_user_names', 'firstName', 'lastName'),
    )


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


class LostItemReport(db.Model):
    
    __tablename__ = 'lost_item_report'

    reportID = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15)) # Increased for flexibility
    date_lost = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Foreign Key
    # Make sure 'User.userID' matches your User model's table/column exactly
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)

    # Relationships
    
    # 1. CRITICAL: This allows the email logic to find the user's email address
    user = db.relationship('User', backref='lost_reports')

    # 2. One-to-One with Description
    # cascade="all, delete-orphan" deletes description if the report is deleted
    description = db.relationship(
        'LostItemDescription', 
        backref='report', 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    # 3. Matches associated with this lost report
    matches = db.relationship('Match', backref='lost_report', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LostItemReport {self.reportID} - User {self.userID}>"

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

    def __repr__(self):
        return f"{self.text_description}"



#Picture should be optional here 
class FoundItemReport(db.Model):
    __tablename__ = 'found_item_report'

    reportID = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15)) # Increased to 15 for international formats/extensions
    date_found = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Office Details
    office_name = db.Column(db.String(100), nullable=False)
    office_directions = db.Column(db.String(255))

    # Foreign Keys
    # Note: Ensure 'User' matches your User model's __tablename__
    adminID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)

    # Relationships
    # 1. Links the report to the admin who filed it
    admin = db.relationship('User', backref='found_reports')

    # 2. One-to-One relationship with the description
    # cascade="all, delete-orphan" ensures if a report is deleted, the description is too
    description = db.relationship(
        'FoundItemDescription', 
        backref='report', 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    # 3. Links to the Match table (Useful for the Dashboard)
    matches = db.relationship('Match', backref='found_report', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FoundItemReport {self.reportID} - {self.office_name}>"


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

    def __repr__(self):
        return f"{self.text_description}"



class Match(db.Model):
    __tablename__ = 'match'

    matchID = db.Column(db.Integer, primary_key=True)
    
    lost_report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'), nullable=False)
    found_report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'), nullable=False)

    similarity_score = db.Column(db.Float, nullable=False) 
    
    #Made into an index for faster retrival 
    status = db.Column(db.String(20), default='pending', index=True) 

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())



class Notification(db.Model):
    __tablename__ = 'notification'

    #Uniquely Identifies Notification 
    notification_id = db.Column(db.Integer, primary_key=True)
    
    #Message attached to Notification 
    message = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    #Links to User 
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'))
    
    #Links to Match 
    match_id = db.Column(db.Integer, db.ForeignKey('match.matchID'))

    #Relationship to User 
    user = db.relationship('User', backref='notifications')