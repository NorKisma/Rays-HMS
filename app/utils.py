from flask import request
from flask_login import current_user
from .models import AuditLog
from .extensions import db

def log_action(action: str, object_type: str = None, object_id: int = None):
    user_id = current_user.id if current_user.is_authenticated else None
    ip_address = request.remote_addr

    audit = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        object_type=object_type,
        object_id=object_id
    )
    db.session.add(audit)
    db.session.commit()
