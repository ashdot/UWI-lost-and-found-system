import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Load variables from .env
load_dotenv()

# cloudinary.config(
#     cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
#     api_key=os.getenv("CLOUDINARY_API_KEY"),
#     api_secret=os.getenv("CLOUDINARY_API_SECRET")
# )

class Config(object):
    """Base Config Object"""
    DEBUG = False

    SECRET_KEY = os.environ.get('SECRET_KEY', 'Som3$ec5etK*y')

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') # Should use this as a fail safe incase cloudinary is down

    cloudinary_url = os.environ.get("CLOUDINARY_URL")

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # This is just here to suppress a warning from SQLAlchemy as it will soon be removed
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))

    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')


