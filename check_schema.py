import sys
import os
sys.path.append(os.getcwd())
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    res = db.session.execute(text("DESCRIBE hospitals")).fetchall()
    for row in res:
        print(row)
