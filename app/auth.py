from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from .models import User
from .forms import LoginForm
from .extensions import db
from datetime import datetime, timezone, timedelta
from werkzeug.security import check_password_hash
from .models import User
import os

auth_bp = Blueprint('auth_bp', __name__)

from werkzeug.security import check_password_hash
from .models import User 

# def verify_user(user_id, user_password):
#     user = User.query.filter_by(userID=user_id).first()


#     if user and check_password_hash(user.password, user_password):
#         return {
#             "role": user.role,
#             "student_id": user.userID,    # Matches model.userID
#             "first_name": user.firstName, # Matches model.firstName
#             "last_name": user.lastName,   # Matches model.lastName
#             "email": user.email
#         }
        
#     return None

def verify_user(user_id, user_password):
    user = User.query.filter_by(userID=user_id).first()
    
    if user:
        # DEBUG PRINTS - Check your terminal!
        print(f"DEBUG: Found user {user.userID}")
        print(f"DEBUG: DB Hash starts with: {user.password[:20]}...")
        
        is_valid = check_password_hash(user.password, user_password)
        print(f"DEBUG: Password match result: {is_valid}")
        
        if is_valid:
            return {
                "role": user.role,
                "student_id": user.userID,
                "first_name": user.firstName,
                "last_name": user.lastName,
                "email": user.email
            }
    else:
        print(f"DEBUG: No user found with ID {user_id}")
        
    return None

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_data = verify_user(form.userID.data, form.password.data)

        if user_data:
            user = User.query.get(user_data["student_id"])
            login_user(user)
            flash(f"Hello, {user.firstName}!", "success")
            return redirect(url_for("views_bp.dashboard"))
        
        flash("Invalid ID or Password", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth_bp.login"))