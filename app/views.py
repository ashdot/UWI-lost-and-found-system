import os
import spacy
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from flask import Blueprint
from .forms import LostItemReportForm, FoundItemReportForm
from .models import LostItemReport, FoundItemReport

#from .extensions import db

views_bp = Blueprint('views_bp', __name__)


#User Authentification - 1st Task 

@views_bp.route("/")
def home():
 return "Hello World"


@views_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


#Note these only work with the database do not delete and do not change 
@views_bp.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    return render_template("admin.html")


@views_bp.route("/report-lost", methods=["GET", "POST"])
@login_required
def report_lost():
    form = LostItemReportForm()

    if form.validate_on_submit():
        lost_item = LostItemReport(
            owner_id=current_user.user_id,
            location_lost=form.location_lost.data,
            date=form.date_lost.data
        )

        db.session.add(lost_item)
        db.session.commit()

        flash("Lost item reported successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("report_lost.html", form=form)


@views_bp.route("/report-found", methods=["GET", "POST"])
@login_required
def report_found():
    if current_user.role != "admin":
        flash("Admins only", "danger")
        return redirect(url_for("dashboard"))

    form = FoundItemReportForm()

    if form.validate_on_submit():
        found_item = FoundItemReport(
            admin_id=current_user.user_id,
            location_found=form.location_found.data,
            date_received=form.date_found.data
        )

        db.session.add(found_item)
        db.session.commit()

        flash("Found item reported", "success")
        return redirect(url_for("dashboard"))

    return render_template("report_found.html", form=form)