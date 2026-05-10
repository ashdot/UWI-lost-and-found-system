import torch
import numpy as np
from app import create_app
from app.extensions import db
from app.models import LostItemReport, FoundItemReport
from app.match import match_lost_found 

def run_test():
    # 1. Initialize the Flask App context
    app = create_app()
    with app.app_context():
        print("\n--- UWI LOST AND FOUND AI TEST ---")
        
        # 2. Grab the latest Lost and Found items from the database
        lost = LostItemReport.query.order_by(LostItemReport.reportID.desc()).first()
        found = FoundItemReport.query.order_by(FoundItemReport.reportID.desc()).first()

        # 3. Validation: Make sure we have data to compare
        if not lost or not found:
            print("❌ ERROR: Database is empty.")
            print("Please go to the website and submit one Lost report and one Found report first.")
            return

        print(f"Comparing Lost Item (ID: {lost.reportID}) vs Found Item (ID: {found.reportID})")
        print(f"Lost Desc:  {lost.description.text_description}")
        print(f"Found Desc: {found.description.text_description}")
        print("-" * 50)

        # 4. Validation: Check for mandatory data
        if lost.description.text_embedding is None:
            print(f"❌ ERROR: Lost Item ID {lost.reportID} is missing a text_embedding!")
            return
        
        if found.description.image_embedding is None:
            print(f"⚠️ WARNING: Found Item ID {found.reportID} is missing an image_embedding!")
            # We don't return here because the algorithm might handle it, 
            # but it's good to know for debugging.

        # 5. Execute the matching algorithm
        try:
            results = match_lost_found(lost, found)

            # 6. Print the breakdown
            print(f"Lost Category:  {results['lost_category']}")
            print(f"Found Category: {results['found_category']}")
            print(f"Category Match: {'✅' if results['category_match'] else '❌'}")
            print("-" * 30)
            
            print(f"Image Score:    {results['image_score']}")
            print(f"Text Score:     {results['text_score']}")
            print(f"Keyword Score:  {results['keyword_score']}")
            print("-" * 30)

            # Showing the status and the threshold used
            status_colors = {
                "high": "🚀  HIGH MATCH",
                "potential": "⚖️  POTENTIAL MATCH",
                "none": "❌  NO MATCH"
            }
            
            current_status = results.get('match_status', 'none')
            print(f"FINAL MATCH SCORE: {results['final_score'] * 100:.2f}%")
            print(f"MATCH STATUS:      {status_colors.get(current_status)}")
            print(f"REQUIRED SCORE:    {results['threshold_used'] * 100:.2f}% (For High Match)")
            print("-" * 30)

            # 7. Final Verdict
            if current_status == "high":
                print("ACTION: System would send AUTOMATIC NOTIFICATIONS.")
            elif current_status == "potential":
                print("ACTION: System would list this as a SUGGESTED MATCH for Admins.")
            else:
                print("ACTION: No action taken.")

        except Exception as e:
            # This captures KeyErrors if match_lost_found doesn't return what we expect
            import traceback
            print(f"❌ ALGORITHM ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_test()