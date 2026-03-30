#from .extensions import db
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash



# class User(db.Model):

#     __tablename__ = 'User'
    
#     userID = db.Column(db.Integer, primary_key=True)

#     firstName = db.Column(db.String(80))
#     lastName = db.Column(db.String(80))

#     email = db.Column(db.String(100))
#     password = db.Column(db.String(128))

#     role = db.Column(db.String(50))


#     failed_attempted = db.Column(db.Integer(0)) 

#     lock_until = db.Column(db.DateTime(timezone=True), nullable=True)

class User: #commented out for testing purposes 
    def __init__(self, firstName, lastName, role , password):
        self.firstName = firstName
        self.lastName = lastName
        self.rol = role
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
        self.failed_attempts += 1
        if self.failed_attempts >= 3:
            self.lock_until = datetime.now(timezone.utc) + timedelta(days=7)


# TO BE DONE -> LOST AND FOUND REPORT MODELS 

# class LostItemReport(db.Model):

#     __tablename__ = 'lost_item_report'

#     reportID = db.Column(db.Integer, primary_key=True)

#     phone = db.Column(db.String(10))

#     date_lost = db.Column(db.DateTime)
#     location_lost = db.Column(db.String(100))

#     description = db.relationship('LostItemDescription', backref='report', uselist=False)


# class LostItemDescription(db.Model):

#     __tablename__ = 'lost_item_description'

#     id = db.Column(db.Integer, primary_key=True)

#     item_type = db.Column(db.String(50))
#     brand = db.Column(db.String(50))
#     color = db.Column(db.String(30))

#     text_description = db.Column(db.Text)
#     text_embedding = db.Column(db.PickleType)

#     report_id = db.Column(db.Integer, db.ForeignKey('lost_item_report.reportID'))

# class FoundItemReport(db.Model):
#     __tablename__ = 'found_item_report'

#     reportID = db.Column(db.Integer, primary_key=True)

#     phone = db.Column(db.String(10))

#     date_found = db.Column(db.DateTime)
#     location_found = db.Column(db.String(100))


#     office_name = db.Column(db.String(100))
#     office_location = db.Column(db.String(100))

#     description = db.relationship('FoundItemDescription', backref='report', uselist=False)

# class FoundItemDescription(db.Model):
    
#     __tablename__ = 'found_item_description'

#     id = db.Column(db.Integer, primary_key=True)

#     item_type = db.Column(db.String(50))
#     brand = db.Column(db.String(50))
#     color = db.Column(db.String(30))

#     text_description = db.Column(db.Text)
#     text_embedding = db.Column(db.PickleType)

#     report_id = db.Column(db.Integer, db.ForeignKey('found_item_report.reportID'))


from datetime import datetime
from typing import Optional

# These are here for testing purposes with text file
# ------------------------
# Lost Item Classes
# ------------------------
class LostItemDescription:
    def __init__(self, item_type: str, brand: str, color: str,
                 text_description: str, text_embedding: Optional[bytes] = None):
        self.id = None  # optional, can assign when saving
        self.item_type = item_type
        self.brand = brand
        self.color = color
        self.text_description = text_description
        self.text_embedding = text_embedding
        self.report = None  # link to LostItemReport


class LostItemReport:
    _id_counter = 1  # simple counter for reportID

    def __init__(self, phone: str, date_lost: datetime, location_lost: str,
                 description: Optional[LostItemDescription] = None):
        self.reportID = LostItemReport._id_counter
        LostItemReport._id_counter += 1

        self.phone = phone
        self.date_lost = date_lost
        self.location_lost = location_lost
        self.description = description
        if description:
            description.report = self


# ------------------------
# Found Item Classes
# ------------------------
class FoundItemDescription:
    def __init__(self, item_type: str, brand: str, color: str,
                 text_description: str, text_embedding: Optional[bytes] = None):
        self.id = None  # optional
        self.item_type = item_type
        self.brand = brand
        self.color = color
        self.text_description = text_description
        self.text_embedding = text_embedding
        self.report = None  # link to FoundItemReport


class FoundItemReport:
    _id_counter = 1  # simple counter for reportID

    def __init__(self, phone: str, date_found: datetime, location_found: str,
                 office_name: str, office_location: str,
                 description: Optional[FoundItemDescription] = None):
        self.reportID = FoundItemReport._id_counter
        FoundItemReport._id_counter += 1

        self.phone = phone
        self.date_found = date_found
        self.location_found = location_found
        self.office_name = office_name
        self.office_location = office_location
        self.description = description
        if description:
            description.report = self