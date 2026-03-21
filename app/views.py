import os
from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required

#User Authentification - 1st Task 

@app.route("/")
def home():
 return "Hello World"