import os
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from .extensions import login_manager
from .views import views_bp
from .auth import auth_bp 



def create_app():
    app = Flask(__name__)

    #For testings
    app.secret_key = "supersecretkey123"

    # Initialize login manager
    login_manager.init_app(app)

    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)

    print(list(app.url_map.iter_rules()))

    # you can add config here later
    # app.config['SECRET_KEY'] = 'your-secret-key'

    return app