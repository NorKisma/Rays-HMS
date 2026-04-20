import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.seed import seed_roles

app = create_app()
with app.app_context():
    seed_roles()
    print("Developer role seeding completed successfully.")
