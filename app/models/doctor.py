from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin

class Doctor(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):

    __tablename__ = "doctors"
    id = db.Column(db.Integer, primary_key=True)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(255))
    experience_years = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    consultation_fee = db.Column(db.Numeric(10, 2))
    availability_status = db.Column(db.String(20), default='available') # available, busy, on_leave
    
    def __repr__(self):
        return f"<Doctor {self.first_name} {self.last_name} ({self.specialization})>"
