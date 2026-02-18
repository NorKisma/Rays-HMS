from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin
from datetime import datetime

class Ward(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'wards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ward_type = db.Column(db.String(50)) # General, ICU, Private, Maternity
    capacity = db.Column(db.Integer, default=0)
    floor = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')

    def __repr__(self):
        return f"<Ward {self.name}>"

class Bed(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'beds'
    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    bed_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available') # available, occupied, maintenance

    ward = db.relationship('Ward', backref=db.backref('beds', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Bed {self.bed_number} - {self.status}>"

class Admission(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'admissions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_date = db.Column(db.DateTime, nullable=True)
    
    reason = db.Column(db.Text)
    initial_diagnosis = db.Column(db.Text)
    status = db.Column(db.String(20), default='admitted') # admitted, discharged, transferred
    
    patient = db.relationship('Patient', backref=db.backref('admissions', lazy=True))
    bed = db.relationship('Bed', backref=db.backref('admissions', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('admissions', lazy=True))

    def __repr__(self):
        return f"<Admission Patient {self.patient_id} Bed {self.bed_id}>"

class NursingNote(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'nursing_notes'
    id = db.Column(db.Integer, primary_key=True)
    admission_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    note_content = db.Column(db.Text, nullable=False)
    temperature = db.Column(db.String(20))
    blood_pressure = db.Column(db.String(20))
    pulse_rate = db.Column(db.String(20))
    
    admission = db.relationship('Admission', backref=db.backref('nursing_notes', lazy=True, order_by="desc(NursingNote.created_at)"))
    staff = db.relationship('User')

    def __repr__(self):
        return f"<Note Adm {self.admission_id} by Staff {self.staff_id}>"
