import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db
from app.blueprints.auth.models import User


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        db.session.add(User(username="admin", role="ADMIN"))
        db.session.add(User(username="user", role="USER"))
        db.session.commit()
        print("Database initialized")
