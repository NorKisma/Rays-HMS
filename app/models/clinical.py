from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin
from datetime import datetime

class PatientVital(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'patient_vitals'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    weight = db.Column(db.String(20))     # e.g., 70kg
    height = db.Column(db.String(20))     # e.g., 170cm
    temperature = db.Column(db.String(20)) # e.g., 37°C
    blood_pressure = db.Column(db.String(20)) # e.g., 120/80
    heart_rate = db.Column(db.String(20)) # e.g., 80 bpm
    respiratory_rate = db.Column(db.String(20)) # e.g., 16 bpm
    spo2 = db.Column(db.String(20))        # Oxygen Saturation e.g., 98%
    
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    note = db.Column(db.Text)

    patient = db.relationship('Patient', backref=db.backref('vitals', lazy=True, order_by="desc(PatientVital.created_at)"))
    staff = db.relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f"<Vital Patient {self.patient_id} - {self.created_at}>"

class Prescription(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    ai_suggestions = db.Column(db.Text) # For AI suggested conditions based on symptoms
    status = db.Column(db.String(20), default='active') # active, completed, cancelled

    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True, order_by="desc(Prescription.created_at)"))
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('clinical_prescription', uselist=False))

    def __repr__(self):
        return f"<Prescription Patient {self.patient_id} Doctor {self.doctor_id}>"

class PrescriptionItem(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'prescription_items'
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    
    medicine_name = db.Column(db.String(150), nullable=False) # Can be free text or linked to inventory
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    dosage = db.Column(db.String(100))    # e.g., 500mg
    frequency = db.Column(db.String(100)) # e.g., 1x3 (three times a day)
    duration = db.Column(db.String(100))  # e.g., 7 days
    instructions = db.Column(db.Text)     # e.g., After meal

    prescription = db.relationship('Prescription', backref=db.backref('items', cascade="all, delete-orphan"))
    product = db.relationship('Product')

    def __repr__(self):
        return f"<PrescriptionItem {self.medicine_name}>"

class Triage(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'triage_records'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    priority_level = db.Column(db.String(20)) # Red (Emergency), Yellow (Urgent), Green (Routine)
    symptoms = db.Column(db.Text)
    triage_notes = db.Column(db.Text)
    
    # Vital snapshot at triage
    temp = db.Column(db.String(10))
    bp = db.Column(db.String(20))
    pulse = db.Column(db.String(10))
    
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, seen_by_doctor

    patient = db.relationship('Patient', backref=db.backref('triage_records', lazy=True, order_by="desc(Triage.created_at)"))
    staff = db.relationship('User')

    def __repr__(self):
        return f"<Triage {self.patient_id} - {self.priority_level}>"

class ChronicCondition(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'chronic_conditions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    condition_name = db.Column(db.String(200), nullable=False)
    on_set_date = db.Column(db.Date)
    severity = db.Column(db.String(50)) # Mild, Moderate, Severe
    status = db.Column(db.String(20), default='active') # active, in_remission, resolved
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', backref=db.backref('chronic_conditions', lazy=True))

    def __repr__(self):
        return f"<Condition {self.condition_name} for Patient {self.patient_id}>"
