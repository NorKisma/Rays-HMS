
from app import create_app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash

def seed_accountant():
    app = create_app()
    with app.app_context():
        # Find the Accountant role
        role = Role.query.filter_by(name='Accountant').first()
        if not role:
            print("❌ Error: 'Accountant' role not found. Please run init_hms_rbac.py first.")
            return

        email = 'accountant@rayshms.com'
        pwd = 'accountant123'
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"✅ User {email} already exists.")
            return

        # Create user
        user = User(
            name='Accountant User',
            email=email,
            password_hash=generate_password_hash(pwd, method='pbkdf2:sha256'),
            is_active=True,
            role_id=role.id
        )
        
        db.session.add(user)
        db.session.commit()
        
        print("=" * 60)
        print("🎉 ACCOUNTANT USER CREATED")
        print("=" * 60)
        print(f"📧 Email:    {email}")
        print(f"🔑 Password: {pwd}")
        print("=" * 60)

if __name__ == "__main__":
    seed_accountant()
