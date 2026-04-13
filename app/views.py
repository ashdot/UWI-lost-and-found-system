import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LostItemReportForm, FoundItemReportForm
from .models import LostItemReport, FoundItemReport, LostItemDescription , FoundItemDescription
from .extensions import login_manager, db 

views_bp = Blueprint('views_bp', __name__)

#User Authentification - 1st Task 

@views_bp .route("/")
def home():
 return "Hello World"

@views_bp .route("/dashboard")
# @login_required #Commented out for testing 
def dashboard():
    return render_template("dashboard.html")


@views_bp .route("/admin")
# @login_required #Commented out for testing 
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    return render_template("admin.html")


@views_bp.route("/report-lost", methods=["GET", "POST"])
def report_lost():
    form = LostItemReportForm()

    if form.validate_on_submit():

        image_url = None
        if form.photo.data:
            # Uploading the file object directly to Cloudinary
            upload_result = cloudinary.uploader.upload(form.photo.data)
            image_url = upload_result.get('secure_url')

        lost_item = LostItemReport(
            phone=form.phone_number.data,
            date_lost=form.date_lost.data,
            location_lost=form.location_lost.data
        )
        
        #Adds lost item to database 
        db.session.add(lost_item)
        db.session.flush() # This populates lost_item.reportID without committing yet

        description = LostItemDescription(
            item_type=form.category.data,
            text_description=form.description.data,
            photo_url=image_url, # <--- Cloudinary URL goes here
            report_id=lost_item.reportID
        )

        #Adds lost item description 
        db.session.add(description)
        db.session.commit()

        flash("Lost item reported successfully", "success")
        return redirect(url_for("views_bp.dashboard"))

    return render_template("report_lost.html", form=form)


@views_bp.route("/report-found", methods=["GET", "POST"])
# @login_required #Commented out for testing 
def report_found():
    if current_user.role != "admin":
        flash("Admins only", "danger")
        return redirect(url_for("dashboard"))

    form = FoundItemReportForm()

    if form.validate_on_submit():
        # 1. Handle Optional Cloudinary Upload
        image_url = None
        if form.photo.data:
            upload_result = cloudinary.uploader.upload(form.photo.data)
            image_url = upload_result.get('secure_url')

        # 2. Create the FoundItemReport (Main Table)
        found_item = FoundItemReport(
            phone=form.phone_number.data, 
            location_found=form.location_found.data,
            date_found=form.date_found.data
        )

        db.session.add(found_item)
        db.session.flush() # Populates found_item.reportID

        # 3. Create the FoundItemDescription (Detail Table)
        description = FoundItemDescription(
            item_type=form.category.data,
            brand=form.brand.data,
            color=form.color.data,
            text_description=form.description.data or "No description",
            photo_url=image_url, # <--- The Cloudinary URL
            report_id=found_item.reportID
        )

        db.session.add(description)
        db.session.commit()

        flash("Found item reported successfully", "success")
        return redirect(url_for("views_bp.dashboard"))

    return render_template("report_found.html", form=form)
