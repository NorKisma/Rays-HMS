import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Role, Permission
from werkzeug.security import generate_password_hash

load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@hms.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def init_permissions():
    """Defines and creates all HMS permissions."""
    permissions = {
        'System': ['manage_users', 'view_logs', 'update_settings'],
        'Patients': ['view_patients', 'add_patients', 'edit_patients', 'delete_patients'],
        'Doctors': ['view_doctors', 'add_doctors', 'edit_doctors'],
        'Appointments': ['view_appointments', 'add_appointments', 'edit_appointments', 'cancel_appointments', 'complete_appointments'],
        'Clinical': ['view_vitals', 'add_vitals', 'add_diagnosis', 'add_prescription'],
        'Billing': ['view_billing', 'create_billing', 'process_payment', 'manage_discounts'],
        'Inventory': ['view_inventory', 'add_inventory', 'edit_inventory', 'adjust_stock'],
        'Sales': ['view_sales', 'process_sales', 'return_sales'],
        'Reports': ['view_reports', 'export_reports']
    }
    
    all_perms = []
    for category, perms in permissions.items():
        for perm_name in perms:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                perm = Permission(name=perm_name, description=f"{category} - {perm_name.replace('_', ' ').title()}")
                db.session.add(perm)
            all_perms.append(perm)
    
    db.session.commit()
    return all_perms

def init_roles(perms):
    """Defines roles and assigns appropriate permissions."""
    
    # helper to get perms by name
    def get_perms(names):
        return [p for p in perms if p.name in names]

    roles_data = {
        'Admin': {
            'description': 'Full System Access',
            'permissions': [p.name for p in perms] # All permissions
        },
        'Doctor': {
            'description': 'Clinical & Patient Management',
            'permissions': [
                'view_patients', 'edit_patients',
                'view_appointments', 'complete_appointments',
                'view_vitals', 'add_vitals', 'add_diagnosis', 'add_prescription',
                'view_inventory'
            ]
        },
        'Nurse': {
            'description': 'Patient Support & Vitals',
            'permissions': [
                'view_patients', 'view_appointments',
                'view_vitals', 'add_vitals',
                'view_inventory'
            ]
        },
        'Receptionist': {
            'description': 'Patient Registration & Scheduling',
            'permissions': [
                'view_patients', 'add_patients', 'edit_patients',
                'view_appointments', 'add_appointments', 'edit_appointments',
                'view_billing', 'create_billing'
            ]
        },
        'Pharmacist': {
            'description': 'Inventory & Medication Management',
            'permissions': [
                'view_inventory', 'add_inventory', 'edit_inventory', 'adjust_stock',
                'view_sales', 'process_sales',
                'view_patients', 'view_reports'
            ]
        },
        'Accountant': {
            'description': 'Financial Management',
            'permissions': [
                'view_billing', 'create_billing', 'process_payment', 'manage_discounts',
                'view_reports', 'export_reports'
            ]
        }
    }

    for role_name, data in roles_data.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=data['description'])
            db.session.add(role)
        
        # Sync permissions
        role_perms = get_perms(data['permissions'])
        role.permissions = role_perms
        print(f"Role '{role_name}' initialized with {len(role_perms)} permissions.")

    db.session.commit()

def init_admin():
    """Creates initial admin user if not exists."""
    admin_role = Role.query.filter_by(name="Admin").first()
    admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()
    
    if not admin_user:
        admin_user = User(
            name="Super Admin",
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role_id=admin_role.id
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user '{ADMIN_EMAIL}' created.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Ensure tables are created for SQLite
        db.create_all()
        
        print("Initializing HMS Permissions...")
        perms = init_permissions()
        print(f"Total {len(perms)} permissions ensured.")
        
        print("Initializing HMS Roles...")
        init_roles(perms)
        
        print("Initializing Admin Account...")
        init_admin()
        
        print("\nRBAC Initialization Complete!")
