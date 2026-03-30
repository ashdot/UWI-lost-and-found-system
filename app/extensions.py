# from flask_sqlalchemy import SQLAlchemy  
# from flask_login import LoginManager       

# db = SQLAlchemy()
# login_manager = LoginManager()

from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"  # redirect to /login if not logged in
