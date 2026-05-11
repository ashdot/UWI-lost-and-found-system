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

from .match import generate_embeddings, match_lost_found

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/admin/dashboard")
@login_required 
def admin_dashboard():
    # 1. Security Check
    if current_user.role != "admin":
        return redirect(url_for("views_bp.dashboard"))
    
    # 2. Retrieve GLOBAL Matches (The Fix)
    # Instead of filtering by the admin's personal ID, get all matches
    matches = Match.query.all()

    # 3. Analytics Section
    total_lost = LostItemReport.query.count()
    total_found = FoundItemReport.query.count()
    pending_claims = Match.query.filter_by(status='pending').count()
    successful_returns = Match.query.filter_by(status='confirmed').count()

    return render_template(
        "admin_dashboard.html", 
        matches=matches,  # Now contains all system matches
        stats={
            "total_lost": total_lost,
            "total_found": total_found,
            "pending_claims": pending_claims,
            "successful_returns": successful_returns
        }
    )

@admin_bp.route('/admin/reports/all')
def view_all_reports():
    if current_user.role != "admin":
        return redirect(url_for("views_bp.dashboard"))

    # Fetching all reports, ordering by most recent first
    lost_reports = LostItemReport.query.order_by(LostItemReport.date_lost.desc()).all()
    found_reports = FoundItemReport.query.order_by(FoundItemReport.date_found.desc()).all()

    return render_template('admin_reports.html', 
                           lost_reports=lost_reports, 
                           found_reports=found_reports)


@admin_bp.route("/admin/manage-claims")
@login_required
def manage_claims():
    if current_user.role != "admin":
        return redirect(url_for("views_bp.dashboard"))

    # Fetch all matches that were claimed by users 
    test = Match.query.all()

    return render_template("admin_claims.html", matches=test)

@admin_bp.route('/match/details/<int:match_id>')
def view_match_details(match_id):
    if current_user.role != "admin":
        return redirect(url_for("views_bp.dashboard"))

    # Fetch the match or return 404 if not found
    match = Match.query.get_or_404(match_id)
    
    lost_report = match.lost_report
    found_report = match.found_report
    
    return render_template('match_details.html', 
                           match=match, 
                           lost=lost_report, 
                           found=found_report)


@admin_bp.route("/match/<int:match_id>/action/<string:action>", methods=["POST"])
@login_required
def handle_match_action(match_id, action):
    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    match = Match.query.get_or_404(match_id)

    if action == "claimed":
        match.status = "confirmed"
        flash("Claim confirmed! The item has been marked as returned.", "success")
    
    elif action == "reject":
        match.status = "rejected"
        flash("Match rejected. It will no longer appear in active claims.", "info")

    db.session.commit()
    return redirect(url_for("admin_bp.admin_dashboard"))


@admin_bp.route("/admin/auto-generate-all-matches", methods=["POST"])
@login_required
def admin_auto_generate_all():
    if current_user.role != "admin":
        flash("Unauthorized: Admins only.", "danger")
        return redirect(url_for("views_bp.dashboard"))

    try:
        all_lost = LostItemReport.query.all()
        all_found = FoundItemReport.query.all()
        new_matches_count = 0

        for lost_item in all_lost:
            # Skip if no description/embeddings yet
            if not lost_item.description:
                continue

            for found_item in all_found:
                if not found_item.description:
                    continue

                # 1. Check if this match already exists in the DB
                existing = Match.query.filter_by(
                    lost_report_id=lost_item.reportID,
                    found_report_id=found_item.reportID
                ).first()
                
                if existing:
                    continue

                # 2. Run your existing AI matching logic
                match_result = match_lost_found(lost_item, found_item)
                
                # 3. If it's a hit, save it
                if match_result["match_status"] in ["high", "potential"]:
                    new_match = Match(
                        lost_report_id=lost_item.reportID,
                        found_report_id=found_item.reportID,
                        similarity_score=match_result["final_score"],
                        status='pending'
                    )
                    db.session.add(new_match)
                    db.session.flush() # Get matchID for notification

                    # 4. Notify the user who lost the item
                    new_notif = Notification(
                        userID=lost_item.userID,
                        message=f"New match found for your {lost_item.description.item_type}!",
                        match_id=new_match.matchID 
                    )
                    db.session.add(new_notif)
                    new_matches_count += 1

        db.session.commit()
        flash(f"System-wide scan complete! {new_matches_count} new matches were generated.", "success")

    except Exception as e:
        db.session.rollback()
        print(f" GLOBAL MATCH ERROR: {e}")
        flash("An error occurred during the global scan.", "danger")

    return redirect(url_for("admin_bp.admin_dashboard"))




