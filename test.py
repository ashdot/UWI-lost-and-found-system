from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():

    user1 = User(
        userID=620160259,
        firstName="Natalie",
        lastName="Morris",
        email="natalie.morris@mymona.uwi.edu",
        password="YgdAdNt",
        role="Student"
    )

    user2 = User(
        userID=620030536,
        firstName="Matthew",
        lastName="Scott",
        email="matthew.scott@mymona.uwi.edu",
        password="UycaL0s",
        role="Student"
    )

    db.session.add_all([user1, user2])
    db.session.commit()

print("Users added!")