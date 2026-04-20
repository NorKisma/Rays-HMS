from .extensions import db
from .models import Role

def seed_roles():
    roles = ["admin", "staff", "user", "developer"]  # <-- Make sure admin and developer exist!

    for r in roles:
        if not Role.query.filter_by(name=r).first():
            db.session.add(Role(name=r))

    db.session.commit()
    print("Roles seeded:", roles)
