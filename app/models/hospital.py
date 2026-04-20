from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin

class Hospital(db.Model, SoftDeleteMixin, TimestampMixin):
    """The Tenant model for SaaS multi-tenancy."""
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False) # For URL-based tenant identification
    
    # Subscription Details & Modules
    plan = db.Column(db.String(50), default='free') # free, pro, enterprise
    subscription_status = db.Column(db.String(20), default='active')
    expiry_date = db.Column(db.DateTime, nullable=True)
    
    # Module Toggles (Feature Flags)
    has_pos = db.Column(db.Boolean, default=True)
    has_pharmacy = db.Column(db.Boolean, default=True)
    has_clinical = db.Column(db.Boolean, default=False)
    has_accounting = db.Column(db.Boolean, default=False)
    has_inventory = db.Column(db.Boolean, default=True)
    has_lab = db.Column(db.Boolean, default=False)
    has_ipd = db.Column(db.Boolean, default=False)

    # Metadata
    logo = db.Column(db.String(255))
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    website = db.Column(db.String(120))

    def __repr__(self):
        return f"<Hospital {self.name} ({self.slug})>"
