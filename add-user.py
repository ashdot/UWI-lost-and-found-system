from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import sqlalchemy
import random

app = create_app()

def generate_bulk_users():
    # Helper lists to create variation
    fnames = ["Alice", "Bob", "Charlie", "Dana", "Edward", "Fiona", "George", "Hannah", "Ian", "Julia"]
    lnames = ["Smith", "Jones", "Brown", "Taylor", "Williams", "Wilson", "Davis", "Clark", "Miller", "Moore"]
    roles = ["student", "staff", "admin"]

    with app.app_context():
        print("⏳ Generating 100 users...")
        clean_hash = generate_password_hash('password123', method='pbkdf2:sha256')
        
        stmt = sqlalchemy.text("""
            INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
            VALUES (:uid, :fname, :lname, :email, :pw, :role)
            ON CONFLICT ("email") DO NOTHING
        """)
        
        count = 0
        for i in range(1, 101):
            # Generate unique data for each of the 100 users
            user_data = {
                "uid": 620000000 + i, # Unique IDs starting from 620000001
                "fname": random.choice(fnames),
                "lname": random.choice(lnames),
                "email": f"user{i}@test.com", # Unique email
                "role": random.choice(roles) if i > 5 else "student", # Assign specific roles or random
                "pw": clean_hash
            }
            
            try:
                result = db.session.execute(stmt, user_data)
                if result.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"❌ Error creating {user_data['email']}: {e}")

        db.session.commit()
        print(f"\n🚀 Done! {count} users added to the database.")
        print("🔑 Default password for all: password123")

if __name__ == "__main__":
    generate_bulk_users()
