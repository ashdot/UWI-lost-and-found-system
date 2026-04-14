import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify 
from flask_login import login_user, logout_user, current_user, login_required

from .forms import LostItemReportForm, FoundItemReportForm
from .models import LostItemReport, FoundItemReport, LostItemDescription, FoundItemDescription, Match
from .extensions import db 
# Import the new unified embedding function
from .match import generate_embeddings, match_lost_found


views_bp = Blueprint('views_bp', __name__)

@views_bp .route("/")
def home():
    return "Hello World"

@views_bp.route("/dashboard")
@login_required 
def dashboard():

    #matches = Match.query.filter_by(lost_report_id=user_report_id)

    return render_template("dashboard.html")

@views_bp.route("/report-lost", methods=["GET", "POST"])
@login_required 
def report_lost():
    form = LostItemReportForm()

    if form.validate_on_submit():
        try:
            # 1. Handle Image Upload
            image_url = None
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data)
                image_url = upload_result.get('secure_url')

            # 2. Generate AI Embeddings (The AI wakes up here)
            embeddings = generate_embeddings(
                text=form.description.data, 
                image_url=image_url
            )

            # 3. Create the Main Report
            lost_item = LostItemReport(
                phone=form.phone_number.data,
                date_lost=form.date_lost.data,
                userID=current_user.userID 
            )
            
            db.session.add(lost_item)
            db.session.flush() 

            # 4. Create the Description with AI Vectors
            description = LostItemDescription(
                item_type=form.category.data,
                text_description=form.description.data,
                photo_url=image_url,
                text_embedding=embeddings["text_vec"],  
                image_embedding=embeddings["image_vec"], 
                report_id=lost_item.reportID
            )

            db.session.add(description)
            db.session.commit()

            flash("Lost item reported successfully!", "success")
            return redirect(url_for("views_bp.dashboard"))

        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {e}")
            flash("Could not save report. Please try again.", "danger")

    return render_template("report_lost.html", form=form)


# @views_bp.route("/report-found", methods=["GET", "POST"])
# @login_required
# def report_found():
#     if current_user.role != "admin":
#         flash("Unauthorized: Admins only.", "danger")
#         return redirect(url_for("views_bp.dashboard"))
    
#     form = FoundItemReportForm()

#     if form.validate_on_submit():
#         try:
#             image_url = None
#             if form.photo.data:
#                 upload_result = cloudinary.uploader.upload(form.photo.data)
#                 image_url = upload_result.get('secure_url')

#             # Generate AI Embeddings
#             embeddings = generate_embeddings(
#                 text=form.description.data, 
#                 image_url=image_url
#             )

#             # --- FIX: Ensure office details are included ---
#             found_item = FoundItemReport(
#                 phone=form.phone_number.data, 
#                 date_found=form.date_found.data,
#                 office_name=form.office_name.data,         # Added this
#                 office_directions=form.office_directions.data, # Added this
#                 adminID=current_user.userID
#             )

#             db.session.add(found_item)
#             db.session.flush()

#             description = FoundItemDescription(
#                 item_type=form.category.data,
#                 text_description=form.description.data or "No description",
#                 photo_url=image_url,
#                 text_embedding=embeddings["text_vec"],  
#                 image_embedding=embeddings["image_vec"], 
#                 report_id=found_item.reportID
#             )

#             db.session.add(description)
#             db.session.commit()

#             flash("Found item registered and indexed for matching!", "success")
#             return redirect(url_for("views_bp.dashboard"))

#         except Exception as e:
#             db.session.rollback()
#             print(f"❌ ERROR: {e}")
#             flash("Error processing found item.", "danger")

#     return render_template("report_found.html", form=form)

@views_bp.route("/report-found", methods=["GET", "POST"])
@login_required
def report_found():
    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    form = FoundItemReportForm()

    if form.validate_on_submit():
        try:

            image_url = None
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data)
                image_url = upload_result.get('secure_url')

            embeddings = generate_embeddings(text=form.description.data, image_url=image_url)

            # 2. Save the Found Report
            found_item = FoundItemReport(
                phone=form.phone_number.data, 
                date_found=form.date_found.data,
                office_name=form.office_name.data,
                office_directions=form.office_directions.data,
                adminID=current_user.userID 
            )
            db.session.add(found_item)
            db.session.flush() # This gives us found_item.reportID before committing

            description = FoundItemDescription(
                item_type=form.category.data,
                text_description=form.description.data or "No description",
                photo_url=image_url,
                text_embedding=embeddings["text_vec"],  
                image_embedding=embeddings["image_vec"], 
                report_id=found_item.reportID
            )
            db.session.add(description)

            # --- THE MATCHING LOOP ---
            all_lost = LostItemReport.query.all()
            for lost_item in all_lost:
                match_result = match_lost_found(lost_item, found_item)
                
                if match_result["is_high_match"]:
                    new_match = Match(
                        lost_report_id=lost_item.reportID,
                        found_report_id=found_item.reportID,
                        similarity_score=match_result["final_score"],
                        status='pending'
                    )
                    db.session.add(new_match)
            # ------------------------------------------

            db.session.commit()
            flash("Found item registered and AI matching complete!", "success")
            return redirect(url_for("views_bp.dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template("report_found.html", form=form)

#Edit/Delete Report 




#Notification Report 




#Data Analytics 





#Error handling 


@views_bp.after_request
def add_header(response):
   """
   Add headers to both force latest IE rendering engine or Chrome Frame,
   and also tell the browser not to cache the rendered page. If we wanted
   to we could change max-age to 600 seconds which would be 10 minutes.
   """
   response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
   response.headers['Cache-Control'] = 'public, max-age=0'
   return response

@views_bp.errorhandler(404)
def page_not_found(error):
   response = {
     'message': 'Error occurred: Contents Not Found!'
   }
   return jsonify(response)