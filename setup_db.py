import sqlalchemy
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import random

app = create_app()

def setup():
    with app.app_context():
        # 1. Enable pgvector extension inside the DB
        print("🛠️ Enabling pgvector extension...")
        db.session.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db.session.commit()

        # 2. Create Tables
        print("🏗️ Creating database tables...")
        db.drop_all() # Fresh start
        db.create_all()

        # 3. Generate 100 Users (Updated with your ID format)
        print("👥 Generating 100 test users...")
        clean_hash = generate_password_hash('password123', method='pbkdf2:sha256')
        
        fnames = ["Alice", "Bob", "Charlie", "Dana", "Edward"]
        lnames = ["Smith", "Jones", "Brown", "Taylor", "Williams"]
        
        for i in range(1, 101):
            user = User(
                userID=620000000 + i,
                firstName=random.choice(fnames),
                lastName=random.choice(lnames),
                email=f"user{i}@test.com",
                role="student" if i > 5 else "admin",
                password=None # We'll set the hash directly below
            )
            user.password = clean_hash 
            db.session.add(user)
        
        db.session.commit()
        print("✅ Setup Complete! You can now run the app.")

if __name__ == "__main__":
    setup()
