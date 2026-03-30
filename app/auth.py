from flask import request, render_template, redirect, url_for, flash
from flask_login import login_user
from .models import User
from .forms import LoginForm
from flask import Blueprint
from datetime import datetime, timezone, timedelta
from .extensions import login_manager
import os

auth_bp = Blueprint("auth_bp", __name__)



@login_manager.user_loader
def load_user(user_id):
    # Flask-Login will call this to get the current_user
    return users_in_memory.get(user_id)


# #Verify user from SAAS_Database
# #=======================================================
# def verify_user(user_id, user_email, user_password):
#     file_path = os.path.join(os.getcwd(), "SAAS_Database.txt")

#     try:
#         with open(file_path, "r") as file:
#             for line in file:
#                 if not line.strip():
#                     continue

#                 role, uid, first_name, last_name, email, password = line.strip().split(",")

#                 if (
#                     user_id == uid and
#                     user_email == email and
#                     user_password == password
#                 ):
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


# #ROUTES FOR AUTHENTIFICATION 
# #=============================================================
# def auth_routes(auth_bp):

#     @auth_bp.route("/login", methods=["GET", "POST"])
#     def login():
#         form = LoginForm()

#         if form.validate_on_submit():

#             user_id = form.uid.data
#             user_email = form.email.data
#             user_password = form.password.data

#             #STEP 1: VERIFY FROM SAAS FILE
#             user_data = verify_user(user_id, user_email, user_password)

#             #STEP 2: CHECK LOCAL DB
#             user = User.query.filter_by(email=user_email).first()

#             if not user:
#                     user = User(
#                         uid = user_id,
#                         email = user_email,
#                         role = "user"
#                     )
#                     db.session.add(user)
#                     db.session.commit()

#             #STEP 3: LOCK CHECK
#             if user.is_locked():
#                 remaining_time = user.lock_until - datetime.now(timezone.utc)

#                 minutes = int(remaining_time.total_seconds() // 60)

#                 flash(f"Account locked. Try again in {minutes} minutes.", "danger")
#                 return redirect(url_for("login"))

#             #STEP 4: PASSWORD CHECK
#             if not user_data:
#                 user.register_failed_attempt()
#                 db.session.commit()

#                 flash(f"Invalid credentials ({user.failed_attempts}/3)", "danger")
#                 return redirect(url_for("login"))

#             #STEP 5: SUCCESSFUL LOGIN
#             user.failed_attempts = 0
#             user.lock_until = None
            
#             user.role = user_data["role"]
#             user.first_name = user_data["first_name"]
#             user.last_name = user_data["last_name"]

#             db.session.commit()

#             login_user(user)

#             flash("Login successful!", "success")
#             return redirect(url_for("dashboard"))

#         return render_template("login.html", form=form)




# -----------------------------
# Verify user from text file
# -----------------------------
def verify_user(user_id, user_email, user_password):
    file_path = os.path.join(os.getcwd(), "SAAS_Database.txt")
    try:
        with open(file_path, "r") as file:
            for line in file:
                if not line.strip():
                    continue
                role, uid, first_name, last_name, email, password = line.strip().split(",")
                if user_id == uid and user_email == email and user_password == password:
                    return {
                        "role": role,
                        "student_id": uid,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email
                    }
    except FileNotFoundError:
        print("SAAS_Database.txt not found")
    return None

# -----------------------------
# Keep users in memory for testing
# -----------------------------
users_in_memory = {}  # key=email, value=User object

# -----------------------------
# Routes
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user_id = form.uid.data
        user_email = form.email.data
        user_password = form.password.data

        # Step 1: Verify from text file
        user_data = verify_user(user_id, user_email, user_password)

        # Step 2: Check local "memory DB"
        user = users_in_memory.get(user_email)
        if not user:
            user = User(uid=user_id, email=user_email, role="user")
            users_in_memory[user_email] = user

        # Step 3: Lock check
        if user.is_locked():
            remaining_time = user.lock_until - datetime.now(timezone.utc)
            minutes = int(remaining_time.total_seconds() // 60)
            flash(f"Account locked. Try again in {minutes} minutes.", "danger")
            return redirect(url_for("auth_bp.login"))

        # Step 4: Password check
        if not user_data:
            user.register_failed_attempt()
            flash(f"Invalid credentials ({user.failed_attempts}/3)", "danger")
            return redirect(url_for("auth_bp.login"))

        # Step 5: Successful login
        user.failed_attempts = 0
        user.lock_until = None
        user.role = user_data["role"]
        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]

        login_user(user)
        flash("Login successful!", "success")
        return redirect(url_for("views_bp.home"))  # redirect to home/dashboard

    return render_template("login.html", form=form)