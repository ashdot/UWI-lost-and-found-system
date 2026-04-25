import os
import cloudinary 
import cloudinary.uploader
from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify 
from flask_login import login_user, logout_user, current_user, login_required

from flask_mail import Message
from sqlalchemy import func

from .forms import LostItemReportForm, FoundItemReportForm
from .models import LostItemReport, FoundItemReport, LostItemDescription, FoundItemDescription, Match, Notification
from .extensions import db, mail

from .match import generate_embeddings, match_lost_found

#Views Blueprint that contains all non-auth views of the Application 
views_bp = Blueprint('views_bp', __name__)

@views_bp .route("/")
def home():
    return "Uwi Lost and Found"

@views_bp.route("/dashboard")
@login_required 
def dashboard():

    if current_user.role == "admin":
        return redirect(url_for("views_bp.admin_dashboard"))

    user_lost_reports = LostItemReport.query.filter_by(userID=current_user.userID).all()
    
    report_ids = [report.reportID for report in user_lost_reports]
    
    matches = Match.query.filter(Match.lost_report_id.in_(report_ids)).all()

    notifications = Notification.query.filter_by(userID=current_user.userID).order_by(Notification.created_at.desc()).all()

    return render_template(
        "dashboard.html", 
        matches=matches, 
        reports=user_lost_reports,
        notifications=notifications
    )

@views_bp.route("/admin/dashboard")
@login_required 
def admin_dashboard():

    #Prevents Non-Admins from Entering Admin Dashboard 
    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))
    
    #Retrieves User Reports 
    user_lost_reports = LostItemReport.query.filter_by(userID=current_user.userID).all()

    report_ids = [r.reportID for r in user_lost_reports]
    
    matches = []
    if report_ids:
        matches = Match.query.filter(Match.lost_report_id.in_(report_ids)).all()

    #Analytics Section - Total Lost, Total Found, Pending Claims, Successful Returns 
    total_lost = LostItemReport.query.count()
    total_found = FoundItemReport.query.count()

    pending_claims = Match.query.filter_by(status='pending').count()
    successful_returns = Match.query.filter_by(status='confirmed').count()

    return render_template(
        "admin_dashboard.html", 
        matches=matches,
        reports=user_lost_reports,
        stats={
            "total_lost": total_lost,
            "total_found": total_found,
            "pending_claims": pending_claims,
            "successful_returns": successful_returns
        }
    )

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

# @views_bp.route("/report-found", methods=["GET", "POST"])
# @login_required
# def report_found():
#     if current_user.role != "admin":
#         flash("Unauthorized: Admins only.", "danger")
#         return redirect(url_for("views_bp.dashboard"))

#     form = FoundItemReportForm()

#     if form.validate_on_submit():
#         try:
#             # 1. Image Upload
#             image_url = None
#             if form.photo.data:
#                 upload_result = cloudinary.uploader.upload(form.photo.data)
#                 image_url = upload_result.get('secure_url')

#             # 2. AI Embedding Generation
#             embeddings = generate_embeddings(text=form.description.data, image_url=image_url)

#             # 3. Create Main Found Report
#             found_item = FoundItemReport(
#                 phone=form.phone_number.data, 
#                 date_found=form.date_found.data,
#                 office_name=form.office_name.data,
#                 office_directions=form.office_directions.data,
#                 adminID=current_user.userID 
#             )
#             db.session.add(found_item)
#             db.session.flush() # Secure the reportID

#             # 4. Create Description Record
#             found_desc = FoundItemDescription(
#                 item_type=form.category.data,
#                 text_description=form.description.data or "No description",
#                 photo_url=image_url,
#                 text_embedding=embeddings["text_vec"],  
#                 image_embedding=embeddings["image_vec"], 
#                 report_id=found_item.reportID
#             )
#             db.session.add(found_desc)
            
#             # CRITICAL FIX: Manually attach description so the Match script can see it immediately
#             found_item.description = found_desc 

#             # 5. THE MATCHING LOOP
#             all_lost = LostItemReport.query.all()
#             matches_found_count = 0
            
#             for lost_item in all_lost:
#                 # Ensure the lost item also has its description loaded
#                 if not lost_item.description:
#                     continue

#                 match_result = match_lost_found(lost_item, found_item)

#                 print(f"DEBUG: Comparing Found {found_item.reportID} with Lost {lost_item.reportID}")
#                 print(f"DEBUG: Final Score: {match_result['final_score']}") 
                
#                 if match_result["is_high_match"]:
#                     new_match = Match(
#                         lost_report_id=lost_item.reportID,
#                         found_report_id=found_item.reportID,
#                         similarity_score=match_result["final_score"],
#                         status='pending'
#                     )
#                     db.session.add(new_match)
#                     matches_found_count += 1

#             db.session.commit()
            
#             if matches_found_count > 0:
#                 flash(f"Success! Item registered and {matches_found_count} potential matches found!", "success")
#             else:
#                 flash("Found item registered. No immediate matches found.", "info")
                
#             return redirect(url_for("views_bp.dashboard"))

#         except Exception as e:
#             db.session.rollback()
#             print(f"❌ DATABASE ERROR: {e}")
#             flash("An error occurred while saving the report.", "danger")

#     # If validation failed, print errors to console for debugging
#     if request.method == 'POST' and not form.validate():
#         print("❌ Validation Errors:", form.errors)

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
            # 1. Image Upload to Cloudinary
            image_url = None
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data)
                image_url = upload_result.get('secure_url')

            # 2. AI Embedding Generation
            embeddings = generate_embeddings(text=form.description.data, image_url=image_url)

            # 3. Create Main Found Report
            found_item = FoundItemReport(
                phone=form.phone_number.data, 
                date_found=form.date_found.data,
                office_name=form.office_name.data,
                office_directions=form.office_directions.data,
                adminID=current_user.userID 
            )
            db.session.add(found_item)
            db.session.flush() # Secures the reportID for the description

            # 4. Create Description Record
            found_desc = FoundItemDescription(
                item_type=form.category.data,
                text_description=form.description.data or "No description",
                photo_url=image_url,
                text_embedding=embeddings["text_vec"],  
                image_embedding=embeddings["image_vec"], 
                report_id=found_item.reportID
            )
            db.session.add(found_desc)
            
            # Attach description so Match script can see it immediately
            found_item.description = found_desc 

            # 5. THE MATCHING LOOP
            all_lost = LostItemReport.query.all()
            potential_matches = []
            
            for lost_item in all_lost:
                if not lost_item.description:
                    continue

                # AI Scoring Logic
                match_result = match_lost_found(lost_item, found_item)
                
                if match_result["is_high_match"]:
                    potential_matches.append({
                        "lost_item": lost_item,
                        "score": match_result["final_score"]
                    })

            # 6. RATE LIMITING & EMAIL NOTIFICATION
            # Sort potential matches by score (highest first)
            potential_matches.sort(key=lambda x: x["score"], reverse=True)

            # Take only the top 3 matches to notify via email
            top_3_matches = potential_matches[:3]
            matches_found_count = len(top_3_matches)

            for match in top_3_matches:
                lost_item = match["lost_item"]
                
                # Save the match to the database
                new_match = Match(
                    lost_report_id=lost_item.reportID,
                    found_report_id=found_item.reportID,
                    similarity_score=match["score"],
                    status='pending'
                )
                db.session.add(new_match)

                new_notif = Notification(
                userID=lost_item.userID,
                message=f"High match found for your {lost_item.description.item_type}!",
                match_id=new_match.matchID 
                )
                db.session.add(new_notif)

                # Send Email Notification
                try:
                    send_match_notification(
                        user_email=lost_item.user.email,
                        item_name=lost_item.description.item_type,
                        office_name=found_item.office_name,
                        directions=found_item.office_directions
                    )
                except Exception as mail_err:
                    print(f"⚠️ Email failed for User {lost_item.userID}: {mail_err}")


            db.session.commit()
            
            if matches_found_count > 0:
                flash(f"Success! Item registered and {matches_found_count} high-quality matches notified!", "success")
            else:
                flash("Found item registered. No immediate matches found.", "info")
                
            return redirect(url_for("views_bp.dashboard"))

        except Exception as e:
            db.session.rollback()
            print(f"❌ DATABASE ERROR: {e}")
            flash("An error occurred while saving the report.", "danger")

    # Debugging validation errors
    if request.method == 'POST' and not form.validate():
        print("❌ Validation Errors:", form.errors)

    return render_template("report_found.html", form=form)





#Edit/Delete Report 

# --- EDIT LOST REPORT ---
@views_bp.route("/report-lost/<int:report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lost_report(report_id):
    report = LostItemReport.query.get_or_404(report_id)

    # Only allow the owner (or admin) to edit
    if report.userID != current_user.userID and current_user.role != "admin":
        flash("Unauthorized: You cannot edit this report.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    form = LostItemReportForm(obj=report)

    if form.validate_on_submit():
        try:
            # Update main report fields
            report.phone = form.phone_number.data
            report.date_lost = form.date_lost.data

            # Handle optional photo update
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data)
                report.description.photo_url = upload_result.get("secure_url")

            # Update description fields
            report.description.item_type = form.category.data
            report.description.text_description = form.description.data

            db.session.commit()
            flash("Lost report updated successfully.", "success")
            return redirect(url_for("views_bp.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating report.", "danger")
            print(f"❌ EDIT ERROR: {e}")

    return render_template("edit_lost.html", form=form, report=report)


# --- DELETE LOST REPORT ---
@views_bp.route("/report-lost/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_lost_report(report_id):
    report = LostItemReport.query.get_or_404(report_id)

    # Only allow the owner (or admin) to edit
    if report.userID != current_user.userID and current_user.role != "admin":
        flash("Unauthorized: You cannot delete this report.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    try:
        db.session.delete(report)
        db.session.commit()
        flash("Lost report deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting report.", "danger")
        print(f"❌ DELETE ERROR: {e}")

    return redirect(url_for("views_bp.dashboard"))


# --- EDIT FOUND REPORT ---
@views_bp.route("/report-found/<int:report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_found_report(report_id):
    report = FoundItemReport.query.get_or_404(report_id)

    # Only admins can edit found reports
    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    form = FoundItemReportForm(obj=report)

    if form.validate_on_submit():
        try:
            report.phone = form.phone_number.data
            report.date_found = form.date_found.data
            report.office_name = form.office_name.data
            report.office_directions = form.office_directions.data

            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data)
                report.description.photo_url = upload_result.get("secure_url")

            report.description.item_type = form.category.data
            report.description.text_description = form.description.data

            db.session.commit()
            flash("Found report updated successfully.", "success")
            return redirect(url_for("views_bp.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating found report.", "danger")
            print(f"❌ EDIT ERROR: {e}")

    return render_template("edit_found.html", form=form, report=report)



# --- DELETE FOUND REPORT ---
@views_bp.route("/report-found/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_found_report(report_id):
    report = FoundItemReport.query.get_or_404(report_id)

    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    try:
        db.session.delete(report)
        db.session.commit()
        flash("Found report deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting report.", "danger")
        print(f"❌ DELETE ERROR: {e}")

    return redirect(url_for("views_bp.dashboard"))


#Notification Function to Send to Email 
def send_match_notification(user_email, item_name, office_name, directions):

    #Message Outline 
    msg = Message(
        subject="Good News! A potential match for your lost item was found",
        sender="noreply@lostandfound.com",
        recipients=[user_email]
    )
    #Message object 
    msg.body = f"Hello! We found a match for your {item_name}. It is being held at {office_name}. Directions: {directions}"
    
    #Sends Message 
    mail.send(msg)


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
