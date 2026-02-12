from app.models import User, db

def create_user(email, password, name, role_id=None):
    user = User(email=email, name=name, role_id=role_id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user
