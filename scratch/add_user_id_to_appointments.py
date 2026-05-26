import sys
import os
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check columns in appointments table
        result = db.session.execute(text("SHOW COLUMNS FROM appointments"))
        columns = [row[0] for row in result.fetchall()]
        print("Current columns in 'appointments':", columns)
        
        if 'user_id' not in columns:
            print("Adding 'user_id' column to 'appointments' table...")
            # Add column
            db.session.execute(text("ALTER TABLE appointments ADD COLUMN user_id INT NULL AFTER hospital_id"))
            # Add foreign key constraint
            db.session.execute(text("ALTER TABLE appointments ADD CONSTRAINT fk_appointments_user_id FOREIGN KEY (user_id) REFERENCES users(id)"))
            db.session.commit()
            print("Column 'user_id' and foreign key constraint added successfully.")
        else:
            print("Column 'user_id' already exists in 'appointments'.")
    except Exception as e:
        print("Error during migration:", e)
