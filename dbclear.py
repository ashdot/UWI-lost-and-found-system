from app import db, create_app
app = create_app()
with app.app_context():
    db.drop_all()   # Deletes any messy old attempts
    db.create_all() # Creates your User, Report, and Vector tables fresh
exit()
