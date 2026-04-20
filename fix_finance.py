from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    tables = ['accounts', 'journal_entries', 'journal_items', 'expenses']
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

    # Specific fix for accounts: remove unique constraint on 'code' if it exists
    try:
        # This is MySQL specific, trying to drop unique index on 'code'
        db.session.execute(text("ALTER TABLE accounts DROP INDEX code"))
        db.session.commit()
        print("SUCCESS: Removed global unique constraint on account code.")
    except:
        db.session.rollback()

    try:
        db.create_all()
        print("SUCCESS: All financial tables synchronized.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
