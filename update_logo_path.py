import sys
import os
sys.path.append(os.getcwd())
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text("UPDATE hospitals SET logo = 'uploads/logos/logo_1.png' WHERE id = 1"))
    db.session.commit()
    print("Database updated: Hospital logo is now active.")
