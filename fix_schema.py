from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    tables = [
        # Inventory
        'categories', 'products', 'batches', 'inventory', 'stock_logs',
        # Billing & Lab
        'billings', 'billing_items', 'lab_requests', 'lab_result_templates', 'lab_tests', 'service_prices',
        # Clinical & Patient Management
        'doctors', 'appointments', 'triage_records', 'admissions',
        # Patients already has it via MultiTenantMixin but re-run is safe
        'patients',
    ]
    for t in tables:
        try:
            db.session.execute(text(f"ALTER TABLE {t} ADD COLUMN hospital_id INT"))
            db.session.execute(text(f"ALTER TABLE {t} ADD CONSTRAINT fk_{t}_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id)"))
            db.session.commit()
            print(f"SUCCESS: Added hospital_id to {t}")
        except Exception as e:
            db.session.rollback()
            if "Duplicate column name" in str(e):
                print(f"INFO: Column hospital_id already exists in {t}")
            elif "Duplicate key name" in str(e) or "already exists" in str(e):
                print(f"INFO: Constraint already exists in {t}")
            else:
                print(f"ERROR updating {t}: {str(e)}")

    try:
        db.create_all()
        print("SUCCESS: Database tables synchronized.")
    except Exception as e:
        print(f"ERROR creating tables: {str(e)}")
