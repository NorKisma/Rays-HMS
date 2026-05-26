import sys
import os
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role.name if u.role else 'None'}")
