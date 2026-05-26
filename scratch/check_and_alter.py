import sys
import os
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check columns in beds table
    try:
        result = db.session.execute(text("SHOW COLUMNS FROM beds"))
        columns = [row[0] for row in result.fetchall()]
        print("Current columns in 'beds':", columns)
        if 'room_number' not in columns:
            print("Adding 'room_number' column to 'beds' table...")
            db.session.execute(text("ALTER TABLE beds ADD COLUMN room_number VARCHAR(20) DEFAULT '1' AFTER ward_id"))
            db.session.commit()
            print("Column 'room_number' added successfully.")
        else:
            print("Column 'room_number' already exists in 'beds'.")
    except Exception as e:
        print("Error working with 'beds' table:", e)
