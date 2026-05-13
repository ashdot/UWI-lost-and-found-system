from flask_login import UserMixin
from .extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from pgvector.sqlalchemy import Vector


class User(UserMixin,db.Model):

    __tablename__ = 'User'
    
    #User Details 
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




class LostItemReport(db.Model):
    
    __tablename__ = 'lost_item_report'

    #Report Details 
    reportID = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15)) # Increased for flexibility
    date_lost = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Foreign Keys
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)

    # Relationships

    #One-to-Many with User 
    user = db.relationship('User', backref='lost_reports')

    #One-to-One with Description
    description = db.relationship(
        'LostItemDescription', 
        backref='report', 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    #One-to-Many with Matches 
    matches = db.relationship('Match', backref='lost_report', cascade="all, delete-orphan",
    passive_deletes=True)

    def __repr__(self):
        return f"<LostItemReport {self.reportID} - User {self.userID}>"

class LostItemDescription(db.Model):
    __tablename__ = 'lost_item_description'

    # Description Details 
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50))
    text_description = db.Column(db.Text)
    
    # Embeddings Stored from CLIP model generate_embeddings() function

    # text_embedding_old = db.Column(db.PickleType, name="text_embedding", nullable=True) 
    # image_embedding_old = db.Column(db.PickleType, name="image_embedding", nullable=True)
    
    text_embed = db.Column(Vector(512), nullable=True) #Used PgVector for faster retrieva; 
    image_embed = db.Column(Vector(512), nullable=True)  

    #Photo URL to link to Cloudinary Cloud 
    photo_url = db.Column(db.String(255), nullable=True)

    #Foreign Key
    report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'))

    def __repr__(self):
        return f"{self.text_description}"



class FoundItemReport(db.Model):
    __tablename__ = 'found_item_report'

    #Report Details 
    reportID = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15)) # Increased to 15 for international formats/extensions
    date_found = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Office Details
    office_name = db.Column(db.String(100), nullable=False)
    office_directions = db.Column(db.String(255))

    # Foreign Keys
    adminID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)

    # Relationships

    # One-to-Many with Admin 
    admin = db.relationship('User', backref='found_reports')

    # 2. One-to-One with Description 
    description = db.relationship(
        'FoundItemDescription', 
        backref='report', 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    # 3. Links to the Match table (Useful for the Dashboard)
    matches = db.relationship('Match', backref='found_report', cascade="all, delete-orphan",
    passive_deletes=True)

    def __repr__(self):
        return f"<FoundItemReport {self.reportID} - {self.office_name}>"


class FoundItemDescription(db.Model):
    __tablename__ = 'found_item_description'

    # Description Details 
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50))
    text_description = db.Column(db.Text, nullable=True)
    
    # Embeddings Stored from CLIP model generate_embeddings() function

    # text_embedding_old = db.Column(db.PickleType, name="text_embedding", nullable=True) 
    # image_embedding_old = db.Column(db.PickleType, name="image_embedding", nullable=True)
    
    text_embed = db.Column(Vector(512), nullable=True) #Used PgVector for faster retrieva; 
    image_embed = db.Column(Vector(512), nullable=True) 
    
    # Photo URL to link to Cloudinary Cloud 
    photo_url = db.Column(db.String(255), nullable=True)

    # Foreign Key 
    report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'))

    def __repr__(self):
        return f"{self.text_description}"



class Match(db.Model):
    __tablename__ = 'match'

    #Match Details 
    matchID = db.Column(db.Integer, primary_key=True)
    
    #Foreign Keys 
    lost_report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID', ondelete="CASCADE"), nullable=False)
    found_report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID', ondelete="CASCADE"), nullable=False)

    similarity_score = db.Column(db.Float, nullable=False) 
    
    #Made into an index for faster retrival 
    status = db.Column(db.String(20), default='pending', index=True) 

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())



class Notification(db.Model):
    __tablename__ = 'notification'

    #Notification Details 
    notification_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    #Foreign Keys 
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.matchID',ondelete="CASCADE"))

    #Relationship to User 
    user = db.relationship('User', backref='notifications')