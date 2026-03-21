from . import db
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash



class User(db.Model):

    __tablename__ = 'User'
    
    userID = db.Column(db.Integer, primary_key=True)

    firstName = db.Column(db.String(80))
    lastName = db.Column(db.String(80))

    email = db.Column(db.String(100))
    password = db.Column(db.String(128))

    role = db.Column(db.String(50))


    failed_attempted = db.Column(db.Integer(0))

    lock_until = db.Column(db.DateTime(timezone=True), nullable=True)

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