# run.py

from app import create_app
from app.extensions import db

app = create_app()

# Automatically create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Run the app in debug mode
    app.run(debug=True, host="0.0.0.0", port=5000)
