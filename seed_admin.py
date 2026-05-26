#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seed Admin User for Rays HMS
Creates the default admin account from .env credentials
"""
import os
from app import create_app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash

def seed_admin():
    """Create admin user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        # Get admin credentials from environment
        admin_email = os.getenv('ADMIN_EMAIL', 'hms.rays@gmail.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'hms1234')
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"✅ Admin user already exists: {admin_email}")
            return
        
        # Get or create Admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(
                name='Admin',
                description='Full system access with administrative privileges'
            )
            db.session.add(admin_role)
            db.session.flush()
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            name='admin',
            is_active=True,
            role_id=admin_role.id
        )
        admin_user.password_hash = generate_password_hash(admin_password, method='pbkdf2:sha256')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("=" * 60)
        print("🎉 ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📧 Email:    {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print("=" * 60)
        print("⚠️  IMPORTANT: Change the default password after first login!")
        print("=" * 60)

if __name__ == '__main__':
    try:
        seed_admin()
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        import traceback
        traceback.print_exc()
