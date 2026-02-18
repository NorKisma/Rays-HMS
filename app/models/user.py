from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app.extensions import db

#===============================
# Mixins
#===============================

class TimestampMixin:
    """Adds created_at and updated_at fields to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SoftDeleteMixin:
    """Adds soft delete functionality."""
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        db.session.add(self)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        db.session.add(self)

#===============================
# Association Table
#===============================

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True)
)

#===============================
# Models
#===============================

class Role(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        backref=db.backref("roles", lazy="dynamic"),
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Role {self.name}>"

class Permission(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Permission {self.name}>"

class User(db.Model, UserMixin, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    role = db.relationship("Role", backref=db.backref("users", lazy=True))
    creator = db.relationship("User", remote_side=[id], backref=db.backref("created_users", lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        if self.password_hash is None:
            return False
        try:
            valid = check_password_hash(self.password_hash, password)
            if valid:
                if not self.password_hash.startswith("pbkdf2:"):
                    self.password_hash = generate_password_hash(password)
                    db.session.commit()
            return valid
        except ValueError:
            return False
            
    def has_permission(self, permission_name):
        """Check if user has a specific permission via their role."""
        if not self.role:
            return False
        # Grant all permissions to admin
        if self.role.name.lower() == 'admin':
            return True
        return any(p.name == permission_name for p in self.role.permissions)

    def __repr__(self):
        return f"<User {self.email}>"

class AuditLog(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45))
    object_type = db.Column(db.String(50), nullable=True) 
    object_id = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", backref=db.backref("audit_logs", lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.action} by User {self.user_id}>"

class CompanySettings(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "company_settings"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    short_name = db.Column(db.String(50))
    logo = db.Column(db.String(255))
    address = db.Column(db.String(255))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(120))

    def __repr__(self):
        return f"<CompanySettings {self.name}>"
