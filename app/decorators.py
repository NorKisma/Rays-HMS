from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

# -------------------------
# Permission decorator
# -------------------------
def permission_required(permission_name):
    """Require a specific permission. Raises 403 if unauthorized."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            # Grant everything to Developer
            if current_user.role and current_user.role.name.lower() == 'developer':
                return f(*args, **kwargs)
                
            if not current_user.role or permission_name not in [p.name for p in current_user.role.permissions]:
                flash(f"You do not have the required permission: {permission_name}", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------
# Role decorator with 403
# -------------------------
def role_required(allowed_roles):
    """Require the user to have one of the allowed roles. Raises 403 if unauthorized."""
    if not isinstance(allowed_roles, (list, tuple, set)):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            user_role_name = getattr(current_user.role, 'name', None)
            # Developer role has access to everything
            if user_role_name and user_role_name.lower() == 'developer':
                return f(*args, **kwargs)

            if user_role_name not in allowed_roles:
                flash("You do not have permission to access this resource.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------
# Admin redirect decorator
# -------------------------
def admin_required(f):
    """
    Protect a route so only admin users can access it.
    Redirects non-admins to dashboard with a flash message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        # Developer or Admin can pass
        if current_user.role.name.lower() not in ["admin", "developer"]:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------
# General role redirect decorator
# -------------------------
def role_redirect_required(*roles):
    """
    Only allow users whose role is in the given list.
    Redirects non-authorized users to dashboard with a flash message.
    Example: @role_redirect_required('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            # Developer role bypass
            if current_user.role.name.lower() == 'developer':
                return f(*args, **kwargs)

            if current_user.role.name.lower() not in [r.lower() for r in roles]:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
