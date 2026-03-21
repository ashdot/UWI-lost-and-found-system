from flask import request, jsonify
from flask_login import login_user
from .models import User
from . import db
from app import app 

#ROUTES FOR AUTHENTIFICATION 

@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if user.is_locked():
        return jsonify({"error": "Account locked"}), 403

    if not user.check_password(data["password"]):
        user.register_failed_attempt()
        db.session.commit()

        return jsonify({
            "error": "Invalid credentials",
            "attempts": user.failed_attempts
        }), 401

    # Success
    user.failed_attempts = 0
    user.lock_until = None
    db.session.commit()

    login_user(user)

    return jsonify({
        "message": "Login successful",
        "user_id": user.user_id,
        "role": user.role
    })