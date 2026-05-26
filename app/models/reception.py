from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin
from datetime import datetime

class VisitorLog(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    """
    Tracks all external visitors, vendors, patient relatives, 
    and general front-desk check-ins at the hospital reception.
    """
    __tablename__ = "visitor_logs"

    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(25))
    purpose = db.Column(db.String(100), nullable=False) # e.g. "Visiting Patient", "Supplier", "Official Business", "Job Interview"
    
    # ID Verification
    id_type = db.Column(db.String(50)) # e.g. "National ID", "Passport", "Driver's License"
    id_number = db.Column(db.String(50))
    
    # Optional patient link (if visiting a patient)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True)
    
    # Check-in details
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    check_out_time = db.Column(db.DateTime, nullable=True)
    
    # Basic health screening for visitors
    temperature = db.Column(db.String(10)) # e.g. "36.5 C"
    symptoms = db.Column(db.Text)
    
    # Administrative tracking
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = db.relationship("Patient", backref=db.backref("visitor_logs", lazy="dynamic"))
    recorder = db.relationship("User", foreign_keys=[recorded_by], backref=db.backref("recorded_visitors", lazy="dynamic"))

    def check_out(self):
        """Mark visitor as checked out."""
        self.check_out_time = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return f"<VisitorLog {self.visitor_name} - {self.purpose}>"


class CallLog(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    """
    Tracks phone inquiries, emergency calls, and general calls 
    managed by reception/front desk operators.
    """
    __tablename__ = "call_logs"

    id = db.Column(db.Integer, primary_key=True)
    caller_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(25), nullable=False)
    call_type = db.Column(db.String(20), nullable=False) # "Incoming", "Outgoing"
    call_category = db.Column(db.String(50)) # "Appointment Booking", "General Inquiry", "Emergency", "Billing Dispute", "Other"
    
    # Action taken/status
    details = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False, nullable=False)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    # Relationships
    recorder = db.relationship("User", foreign_keys=[recorded_by], backref=db.backref("recorded_calls", lazy="dynamic"))

    def __repr__(self):
        return f"<CallLog {self.caller_name} - {self.call_category}>"
