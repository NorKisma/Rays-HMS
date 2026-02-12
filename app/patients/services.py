from app.models import Patient, db

def add_patient(data):
    patient = Patient(**data)
    db.session.add(patient)
    db.session.commit()
    return patient
