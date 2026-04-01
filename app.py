import os
from flask import Flask
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required



app = Flask(__name__)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)