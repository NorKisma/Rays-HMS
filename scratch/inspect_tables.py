import sys
import os
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    for table in ['appointments', 'billings', 'patients']:
        result = db.session.execute(text(f"SHOW COLUMNS FROM {table}"))
        columns = [row[0] for row in result.fetchall()]
        print(f"Columns in '{table}':", columns)
