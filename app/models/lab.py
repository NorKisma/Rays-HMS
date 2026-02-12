from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin

class LabRequest(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "lab_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)
    test_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    result = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending") # pending, completed, reviewed
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    appointment = db.relationship("Appointment", backref=db.backref("lab_requests", lazy=True))
    technician = db.relationship("User", backref="lab_tests_performed")
    
    def __repr__(self):
        return f"<LabRequest {self.test_name} - {self.status}>"
