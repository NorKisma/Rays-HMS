import sys
import os
sys.path.append(os.getcwd())
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text("UPDATE hospitals SET name = 'RTC Hospital' WHERE slug = 'default'"))
    db.session.commit()
    print("Database updated: Hospital name is now 'RTC Hospital'")
