from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import sqlalchemy

app = create_app()

def generate_bulk_users():
    users_to_create = [
        {"uid": 620000001, "fname": "Alice", "lname": "Admin", "email": "admin@test.com", "role": "admin"},
        {"uid": 620111222, "fname": "Bob", "lname": "Student", "email": "bob@test.com", "role": "student"},
        {"uid": 620333444, "fname": "Charlie", "lname": "Staff", "email": "charlie@test.com", "role": "staff"},
        {"uid": 620555666, "fname": "Dana", "lname": "Smith", "email": "dana@test.com", "role": "student"},
        {"uid": 620777888, "fname": "Edward", "lname": "Jones", "email": "edward@test.com", "role": "staff"}
    ]

    with app.app_context():
        # Pre-generate the password hash once to save time
        clean_hash = generate_password_hash('password123', method='pbkdf2:sha256')
        
        stmt = sqlalchemy.text("""
            INSERT INTO "User" ("userID", "firstName", "lastName", "email", "password", "role") 
            VALUES (:uid, :fname, :lname, :email, :pw, :role)
            ON CONFLICT ("email") DO NOTHING
        """)
        
        count = 0
        for user_data in users_to_create:
            try:
                # Add the shared password hash to the dictionary
                user_data['pw'] = clean_hash
                
                result = db.session.execute(stmt, user_data)
                
                # Check if a row was actually inserted
                if result.rowcount > 0:
                    print(f"✅ Created: {user_data['email']} ({user_data['role']})")
                    count += 1
                else:
                    print(f"⏩ Skipped: {user_data['email']} (already exists)")
                    
            except Exception as e:
                print(f"❌ Error creating {user_data['email']}: {e}")
        
        db.session.commit()
        print(f"\n🚀 Done! {count} new users added to the database.")
        print("🔑 Default password for all: password123")

if __name__ == "__main__":
    generate_bulk_users()