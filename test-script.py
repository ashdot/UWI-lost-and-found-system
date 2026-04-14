import torch
import numpy as np
from app import create_app
from app.extensions import db
from app.models import LostItemReport, FoundItemReport
from app.match import match_lost_found 


#CREATED USING GEMINI TO TEST THE MATCHING 
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

        # 4. Validation: Make sure they have embeddings saved
        if lost.description.text_embedding is None:
            print(f"❌ ERROR: Lost Item ID {lost.reportID} is missing a text_embedding!")
            return
        if found.description.text_embedding is None:
            print(f"❌ ERROR: Found Item ID {found.reportID} is missing a text_embedding!")
            return

        # 5. Execute the matching algorithm
        try:
            results = match_lost_found(lost, found)

            # 6. Print the breakdown
            print(f"Category Match: {'✅' if results['final_score'] > 0 else '❌'}")
            print(f"Image Score:    {results['image_score']}")
            print(f"Text Score:     {results['text_score']}")
            print(f"Keyword Score:  {results['keyword_score']}")
            print("-" * 30)
            print(f"FINAL MATCH SCORE: {results['final_score'] * 100:.2f}%")
            print("-" * 30)

            if results['is_high_match']:
                print("🚀 RESULT: This is a HIGH MATCH! The Admin should be notified.")
            else:
                print("⚖️ RESULT: Low similarity detected.")

        except Exception as e:
            print(f"❌ ALGORITHM ERROR: {e}")

if __name__ == "__main__":
    run_test()