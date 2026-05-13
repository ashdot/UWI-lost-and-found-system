import os
import cloudinary 
import cloudinary.uploader
from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify 
from flask_login import current_user, login_required

from flask_mail import Message
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from .forms import LostItemReportForm, FoundItemReportForm
from .models import LostItemReport, FoundItemReport, LostItemDescription, FoundItemDescription, Match, Notification
from .extensions import db, mail


from .match import generate_embeddings, match_lost_found # -> LOCAL VERSION WITH PGVECTOR


#Views Blueprint that contains all non-auth views of the Application 
views_bp = Blueprint('views_bp', __name__)


# --- REDIRECT TO LOGIN PAGE ---
@views_bp.route("/")
def home():
    return redirect(url_for('auth_bp.login'))

# --- DASHBOARDS AND CLAIM MANAGEMENT ---
@views_bp.route("/dashboard")
@login_required 
def dashboard():
    """
    Dashboard for General User 
    """
    if current_user.role == "admin":
        return redirect(url_for("admin_bp.admin_dashboard"))

    #Identify which lost reports belong to the user
    user_lost_reports = LostItemReport.query.filter_by(userID=current_user.userID).all()
    report_ids = [report.reportID for report in user_lost_reports]
    
    #Grab matches with ALL nested data 
    matches = Match.query.filter(Match.lost_report_id.in_(report_ids))\
        .options(
            joinedload(Match.found_report)      # Go to the Found Report
            .joinedload(FoundItemReport.description) # Go to the Description (where photo_url is)
        ).all()

    notifications = Notification.query.filter_by(userID=current_user.userID)\
        .order_by(Notification.created_at.desc()).all()

    return render_template(
        "dashboard.html", 
        matches=matches, 
        reports=user_lost_reports,
        notifications=notifications
    )


#FIX CLAIM MANAGEMENT IMPLEMENTAION 
@views_bp.route("/claim-item/<int:match_id>", methods=["POST"])
@login_required
def claim_item(match_id):
    match = Match.query.get_or_404(match_id)
    
    print(f"DEBUG: User {current_user.userID} is trying to claim match {match_id}")
    print(f"DEBUG: Match owner is {match.lost_report.userID}")

    if match.lost_report.userID != current_user.userID:
        print("DEBUG: Unauthorized access - IDs do not match!")
        flash("Unauthorized action.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    match.status = 'claimed'
    db.session.commit() # MAKE SURE THIS LINE IS HERE
    print("DEBUG: Status updated to 'claimed' and committed!")
    
    flash("Claimed successfully!", "success")
    return redirect(url_for("views_bp.dashboard"))
    

# ---VIEW LOST REPORTS --- 
@views_bp.route("/lost_report/<int:report_id>")
@login_required
def view_lost_report(report_id):
    # Ensure the report belongs to the current user
    report = LostItemReport.query.filter_by(
        reportID=report_id,
        userID=current_user.userID
    ).first_or_404()

    # Debug: show report and description
    print("DEBUG: Loaded report:", report)
    print("DEBUG: Report description:", report.description)
    if report.description:
        print("DEBUG: Item type:", report.description.item_type)
        print("DEBUG: Text description:", report.description.text_description)
        print("DEBUG: Photo URL:", report.description.photo_url)

    # Grab matches for this report with nested data
    matches = Match.query.filter_by(lost_report_id=report.reportID)\
        .options(
            joinedload(Match.found_report)
            .joinedload(FoundItemReport.description)
        ).all()

    # Debug: show matches
    print("DEBUG: Matches count:", len(matches))
    for m in matches:
        print("DEBUG: Match:", m)
        print("DEBUG: Status:", m.status)
        print("DEBUG: Found report:", m.found_report)
        if m.found_report and m.found_report.description:
            print("DEBUG: Found item type:", m.found_report.description.item_type)
            print("DEBUG: Found text description:", m.found_report.description.text_description)
            print("DEBUG: Found photo URL:", m.found_report.description.photo_url)

    return render_template(
        "view_lost_report.html",
        report=report,
        matches=matches
    )


# ---REPORT CREATION ---
@views_bp.route("/report-lost", methods=["GET", "POST"])
@login_required 
def report_lost():
    form = LostItemReportForm()

    if form.validate_on_submit():

        if request.method == 'POST':
            print("!!! FORM VALIDATION FAILED !!!")
            print(f"Errors: {form.errors}")
            print(f"Data received: {request.form}")
        try:
            # 1. Handle Image Upload
            image_url = None
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data,folder="uwi_lost_and_found/lost_items")
                image_url = upload_result.get('secure_url')

            # 2. Generate AI Embeddings (The AI wakes up here)
            embeddings = generate_embeddings(
                text=form.description.data, 
                image_url=image_url
            )

            print(f"DEBUG: text_vec type: {type(embeddings['text_vec'])}")
            if embeddings['text_vec']:
                print(f"DEBUG: text_vec length: {len(embeddings['text_vec'])}")

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

                #Save to the OLD pickle columns (as your backup)
                # text_embedding_old=embeddings["text_vec"],
                # image_embedding_old=embeddings["image_vec"],

                text_embed=embeddings["text_vec"],  
                image_embed=embeddings["image_vec"], 
                report_id=lost_item.reportID
            )

            db.session.add(description)
            db.session.commit()

            flash("Lost item reported successfully!", "success")
            return redirect(url_for("views_bp.dashboard"))

        except Exception as e:
            db.session.rollback()
            print(f" ERROR: {e}")
            flash("Could not save report. Please try again.", "danger")

    return render_template("report_lost.html", form=form)


@views_bp.route("/report-found", methods=["GET", "POST"])
@login_required
def report_found():
    if current_user.role != "admin":
        #flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    form = FoundItemReportForm()

    if form.validate_on_submit():
        try:
            # 1. Image Upload to Cloudinary
            image_url = None
            if form.photo.data:
                upload_result = cloudinary.uploader.upload(form.photo.data, folder="uwi_lost_and_found/found_items")

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
                # text_embedding_old=embeddings["text_vec"],
                # image_embedding_old=embeddings["image_vec"],
                text_embed=embeddings["text_vec"],  
                image_embed=embeddings["image_vec"], 
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
                
                if match_result["match_status"] in ["high", "potential"]:
                    potential_matches.append({
                        "lost_item": lost_item,
                        "score": match_result["final_score"],
                        "status": match_result["match_status"] # Store status for notification clarity
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
                message=f"High match found for your item in {lost_item.description.item_type}!",
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
            print(f" DATABASE ERROR: {e}")
            flash("An error occurred while saving the report.", "danger")

    # Debugging validation errors
    if request.method == 'POST' and not form.validate():
        print("Validation Errors:", form.errors)

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
                upload_result = cloudinary.uploader.upload(form.photo.data, folder="uwi_lost_and_found/lost_items")
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

    # Ensures only admins can edit found reports
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
                upload_result = cloudinary.uploader.upload(form.photo.data, folder="uwi_lost_and_found/found_items")
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


#Checks matches in the database 
@views_bp.cli.command("list-matches")
def list_matches():
    """Prints all matches in the database with their categories."""
    matches = Match.query.all()
    
    # Header
    print(f"{'ID':<4} | {'Category':<15} | {'LostID':<7} | {'FoundID':<8} | {'Score':<8} | {'Status'}")
    print("-" * 65)
    
    for m in matches:
        # We pull the category from the lost_report's description
        # Using getattr as a safety net in case a report was deleted
        category = "Unknown"
        if m.lost_report and m.lost_report.description:
            category = m.lost_report.description.item_type
            
        print(f"{m.matchID:<4} | {category:<15} | {m.lost_report_id:<7} | {m.found_report_id:<8} | {m.similarity_score:<8.4f} | {m.status}")

#Checks items in the database 
@views_bp.cli.command("list-items")
def list_items():
    """Prints all Lost and Found items currently in the database."""
    from .models import LostItemReport, FoundItemReport
    
    # --- LOST ITEMS SECTION ---
    print("\n=== LOST ITEMS REPORTS ===")
    lost_items = LostItemReport.query.all()
    if not lost_items:
        print("No lost items reported.")
    else:
        print(f"{'ID':<4} | {'Category':<15} | {'Date Lost':<12} | {'Description'}")
        print("-" * 70)
        for item in lost_items:
            # Accessing the related description object
            cat = item.description.item_type if item.description else "N/A"
            desc = (item.description.text_description[:40] + "...") if item.description else "No desc"
            print(f"{item.reportID:<4} | {cat:<15} | {str(item.date_lost):<12} | {desc}")

    # --- FOUND ITEMS SECTION ---
    print("\n=== FOUND ITEMS REPORTS ===")
    found_items = FoundItemReport.query.all()
    if not found_items:
        print("No found items reported.")
    else:
        print(f"{'ID':<4} | {'Category':<15} | {'Office/Loc':<15} | {'Description'}")
        print("-" * 70)
        for item in found_items:
            cat = item.description.item_type if item.description else "N/A"
            office = item.office_name if item.office_name else "N/A"
            desc = (item.description.text_description[:40] + "...") if item.description else "No desc"
            print(f"{item.reportID:<4} | {cat:<15} | {office:<15} | {desc}")
    print("\n")


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
