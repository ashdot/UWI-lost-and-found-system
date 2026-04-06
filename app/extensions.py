from flask_sqlalchemy import SQLAlchemy  
from flask_login import LoginManager     
from flask_migrate import Migrate  

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
login_manager.login_view = "auth_bp.login"  # redirect to /login if not logged in
