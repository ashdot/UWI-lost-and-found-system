import os
from flask import Flask

from .extensions import db, login_manager, migrate, mail
from .views import views_bp
from .auth import auth_bp 
from .models import User
from .config import Config 



def create_app():
    app = Flask(__name__) #intializes the flask app

    app.config.from_object(Config) #gets configuration of app 

    db.init_app(app) #initalizes the postgres database

    migrate.init_app(app, db) #initializes flask migrate 

    login_manager.init_app(app)

    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)

    mail.init_app(app)

    print(list(app.url_map.iter_rules()))

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Flask-Login expects user_id as a string