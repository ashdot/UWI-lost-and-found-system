from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user
from .models import User
from .forms import LoginForm
from .extensions import db
from datetime import datetime, timezone, timedelta
import os

auth_bp = Blueprint('auth_bp', __name__)

# Verify user from SAAS_Database
# def verify_user(user_id, user_email, user_password):
#     file_path = os.path.join(os.getcwd(), "SAAS_Database.txt")
#     try:
#         with open(file_path, "r") as file:
#             for line in file:
#                 if not line.strip():
#                     continue
#                 role, uid, first_name, last_name, email, password = line.strip().split(",")
#                 if user_id == uid and user_email == email and user_password == password:
#                     return {
#                         "role": role,
#                         "student_id": uid,
#                         "first_name": first_name,
#                         "last_name": last_name,
#                         "email": email
#                     }
#     except FileNotFoundError:
#         print("User not found")
#     return None

def verify_user(user_id, user_password):
    file_path = os.path.join(os.getcwd(), "SAAS_Database.txt")
    try:
        with open(file_path, "r") as file:
            for line in file:
                if not line.strip():
                    continue
                role, uid, first_name, last_name, email, password = line.strip().split(",")
                if user_id == uid and user_password == password:
                    return {
                        "role": role,
                        "student_id": uid,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email
                    }
    except FileNotFoundError:
        print("User not found")
    return None

# ======= Routes =======

#Create a register route for admin ( ASH MONDAY )
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    pass







@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.userID.data
        #user_email = form.email.data
        user_password = form.password.data

        user_data = verify_user(user_id, user_password)
        #user_data = verify_user(user_id, user_email, user_password)
        #user = User.query.filter_by(email=user_email).first()

        user = User.query.filter_by(userID=user_id).first()

        if not user:
            #user = User(uid=user_id, email=user_email, role="user")
            user = User(userID=user_id, role="user")
            db.session.add(user)
            db.session.commit()

        # Lock check
        if user.is_locked():
            remaining_time = user.lock_until - datetime.now(timezone.utc)
            minutes = int(remaining_time.total_seconds() // 60)
            flash(f"Account locked. Try again in {minutes} minutes.", "danger")
            return redirect(url_for("auth_bp.login"))  # note blueprint prefix

        # Password check
        if not user_data:
            user.register_failed_attempt()
            db.session.commit()
            flash(f"Invalid credentials ({user.failed_attempted}/3)", "danger")
            return redirect(url_for("auth_bp.login"))

        # Successful login
        user.failed_attempted = 0
        user.lock_until = None
        user.role = user_data["role"]
        user.firstName = user_data["first_name"]
        user.lastName = user_data["last_name"]
        db.session.commit()

        login_user(user)
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))  # make sure this route exists

    return render_template("login.html", form=form)