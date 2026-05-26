import sys
import os
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check columns in billings table
        result = db.session.execute(text("SHOW COLUMNS FROM billings"))
        columns = [row[0] for row in result.fetchall()]
        print("Current columns in 'billings':", columns)
        
        if 'user_id' not in columns:
            print("Adding 'user_id' column to 'billings' table...")
            # Add column
            db.session.execute(text("ALTER TABLE billings ADD COLUMN user_id INT NULL AFTER hospital_id"))
            # Add foreign key constraint
            db.session.execute(text("ALTER TABLE billings ADD CONSTRAINT fk_billings_user_id FOREIGN KEY (user_id) REFERENCES users(id)"))
            db.session.commit()
            print("Column 'user_id' and foreign key constraint added successfully to 'billings'.")
        else:
            print("Column 'user_id' already exists in 'billings'.")
    except Exception as e:
        print("Error during migration:", e)
