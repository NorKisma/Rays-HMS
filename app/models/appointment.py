from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin

class Appointment(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):

    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True, nullable=False) # e.g. APT-0001
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default="scheduled") # scheduled, completed, cancelled, no_show
    vitals_temperature = db.Column(db.String(10))
    vitals_blood_pressure = db.Column(db.String(20))
    vitals_weight = db.Column(db.String(10))
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    patient = db.relationship("Patient", backref=db.backref("appointments", lazy=True))
    doctor = db.relationship("Doctor", backref=db.backref("appointments", lazy=True))
    user = db.relationship("User", backref=db.backref("appointments", lazy=True))
    
    def __repr__(self):
        return f"<Appointment {self.appointment_number} - Patient {self.patient_id}>"
