#create_admin.py
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Role, Permission
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

# Admin credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "nor.jws@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123123")

# Predefined roles and their permissions
ROLES_PERMISSIONS = {
    "Admin": ["update_settings", "view_dashboard", "manage_users", "view_reports"],
    "Manager": ["view_dashboard", "view_reports", "manage_inventory"],
    "Staff": ["view_dashboard", "manage_sales"]
}

app = create_app()
with app.app_context():
    for role_name, perms in ROLES_PERMISSIONS.items():
        # --- Create or get role ---
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name} role")
            db.session.add(role)
            db.session.commit()
            print(f"Role '{role_name}' created.")
        else:
            print(f"Role '{role_name}' already exists.")

        # --- Create permissions and link to role ---
        for perm_name in perms:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                perm = Permission(name=perm_name)
                db.session.add(perm)
                db.session.commit()
                print(f"Permission '{perm_name}' created.")
            else:
                print(f"Permission '{perm_name}' already exists.")

            if perm not in role.permissions:
                role.permissions.append(perm)
        db.session.commit()

    # --- Create admin user and assign Admin role ---
    admin_role = Role.query.filter_by(name="Admin").first()
    admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin_user:
        admin_user = User(
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD, method="pbkdf2:sha256"),
            role_id=admin_role.id
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user '{ADMIN_EMAIL}' created.")
    else:
        print(f"Admin user '{ADMIN_EMAIL}' already exists.")
