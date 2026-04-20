from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import urlparse, urljoin
from functools import wraps
from flask_wtf import FlaskForm
from datetime import datetime
from sqlalchemy import or_ # Needed for the search filter
from ..models import User, Role
# Import from your application
from . import bp 
from .forms import LoginForm, RegisterForm, ChangePasswordForm, EditUserForm
from ..models import User, Role, Permission # Assuming User and Role models are in ../models.py
from ..extensions import db, limiter
from ..utils import log_action
from .forms import LoginForm, RegisterForm, ChangePasswordForm, EditUserForm, RoleForm

# Constants
DEFAULT_HASH_SCHEME = "pbkdf2:sha256"

# ----------------------------------
# Helper Functions
# ----------------------------------
def is_safe_url(target):
    """
    Checks if a target URL is safe for redirection.
    Prevents Open Redirect vulnerabilities.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

def verify_and_upgrade_password(user, password: str) -> bool:
    """
    Verifies the password and upgrades the hash scheme if necessary.
    Returns True if the password is correct, False otherwise.
    """
    # Assuming the User model has a 'password_hash' attribute
    stored_hash = user.password_hash 
    if check_password_hash(stored_hash, password):
        # Check for hash upgrade
        if not stored_hash.startswith(DEFAULT_HASH_SCHEME):
            user.password_hash = generate_password_hash(password, method=DEFAULT_HASH_SCHEME)
            db.session.commit()
        return True
    return False

# ----------------------------------
# Decorators
# ----------------------------------
def role_required(*roles):
    """
    A decorator that restricts access to a route to users with specified roles.
    Example: @role_required('admin', 'moderator')
    
    NOTE: This implementation relies on the User model having a ONE-TO-ONE/MANY relationship
          named 'role' (singular).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()

            user_role_name = getattr(current_user.role, 'name', '').lower()
            # Developer role bypass
            if user_role_name == 'developer':
                return f(*args, **kwargs)

            allowed_roles = [r.lower() for r in roles]
            if user_role_name not in allowed_roles:
                flash("You do not have permission to access this resource.", "danger")
                return redirect(url_for('main.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------------------------
# Routes
# ----------------------------------
@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and verify_and_upgrade_password(user, password):
            login_user(user)
            log_action("User logged in", object_type="User", object_id=user.id)
            flash("Logged in successfully.", "success")

            # Handle safe redirection to the 'next' parameter
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            current_app.logger.warning(f"Login failed for: {email}")
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)

@bp.route("/logout")
@login_required
def logout():
    """Handles user logout."""
    user_id = current_user.id
    try:
        logout_user()
        log_action("User logged out", object_type="User", object_id=user_id)
        flash("Logged out successfully.", "info")
    except Exception as e:
        current_app.logger.error(f"Logout error for user {user_id}: {e}")
        flash("An error occurred while logging out.", "danger")

    return redirect(url_for("landing.home"))

DEFAULT_HASH_SCHEME = "pbkdf2:sha256"


@bp.route("/register", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def register():
    """Handles new user registration. Only accessible to 'admin' and 'manager' roles."""
    form = RegisterForm()

    # 🌟 Populate role choices (excluding admin)
    try:
        if current_user.role.name.lower() == 'developer':
            available_roles = Role.query.all()
        else:
            available_roles = Role.query.filter(Role.name != "admin", Role.name != "developer").all()
        form.role_id.choices = [(r.id, r.name.title()) for r in available_roles]
    except Exception as e:
        current_app.logger.error(f"Error fetching roles: {e}")
        form.role_id.choices = []

    if form.validate_on_submit():
        name = form.name.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        selected_role_id = form.role_id.data

        # Prevent duplicate registrations
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("auth/register.html", form=form)

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password, method=DEFAULT_HASH_SCHEME),
            role_id=selected_role_id
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            log_action(
                "New user registered ",
                object_type="User",
                object_id=new_user.id
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}")
            flash("An error occurred during registration.", "danger")

    return render_template("auth/register.html", form=form)

@bp.route("/change-password", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per 15 minutes")
def change_password():
    """Handles changing the current user's password."""
    form = ChangePasswordForm()

    # Basic check for a soft-deleted/deactivated account property
    if hasattr(current_user, 'is_deleted') and current_user.is_deleted:
        flash("Your account is deactivated. Contact admin.", "danger")
        return redirect(url_for("main.dashboard"))

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data

        # 1. Check current password (assuming check_password is a method on the User model)
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html", form=form)

        # 2. Check if new password is the same as current
        if current_user.check_password(new_password):
            flash("New password cannot be the same as the current password.", "warning")
            return render_template("auth/change_password.html", form=form)

        # Update and commit (assuming set_password is a method on the User model)
        current_user.set_password(new_password)
        db.session.commit()

        log_action("User changed password", object_type="User", object_id=current_user.id)

        # Re-log the user in with a fresh session (security best practice after password change)
        login_user(current_user, fresh=True)

        flash("Password updated successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/change_password.html", form=form)

# ----------------------------------
# User Management Routes
# ----------------------------------
class DummyForm(FlaskForm):
    pass


# ... (imports remain the same) ...

@bp.route("/users")
@login_required
@role_required("admin", "manager")
def list_users():
    """Display a paginated, searchable, sortable, and filterable list of users."""
    
    # Query parameters
    page = request.args.get("page", 1, type=int) 
    search = request.args.get("search", "", type=str)
    sort = request.args.get("sort", "newest", type=str)
    current_role_filter = request.args.get("roles", "", type=str)
    
    # NEW: Filter for active status (optional)
    active_filter = request.args.get("active", "", type=str)

    # Base query - JOIN using the singular 'role' attribute (One-to-Many fix)
    query = User.query.join(User.role, isouter=True) 

    # --- Search ---
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))

    # --- Role Filter ---
    if current_role_filter:
        query = query.filter(Role.name == current_role_filter)
        
    # --- NEW Active Filter ---
    if active_filter == "active":
        query = query.filter(User.is_active == True)
    elif active_filter == "inactive":
        query = query.filter(User.is_active == False)
    
    # --- Sorting ---
    if sort == "name_asc":
        query = query.order_by(User.name.asc())
    elif sort == "name_desc":
        query = query.order_by(User.name.desc())
    # NEW: Sorting by created_at
    elif sort == "created_asc":
        query = query.order_by(User.created_at.asc())
    elif sort == "created_desc":
        query = query.order_by(User.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(User.id.asc())
    else: 
       # Default sorting to newest created_at (if available), otherwise by ID
       if hasattr(User, 'created_at'):
           query = query.order_by(User.created_at.desc())
       else:
           query = query.order_by(User.id.desc())
        
    # Fetch all users for DataTables
    users = query.distinct().all()

    # For dropdown filter
    roles = Role.query.order_by(Role.name).all()

    return render_template(
        "auth/users.html",
        users=users,
        search=search,
        sort=sort,
        role_filter=current_role_filter, 
        active_filter=active_filter,
        roles=roles,
        csrf_form=DummyForm(),
    )


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def edit_user(user_id):
    """Edit a user's details."""
    user = User.query.get_or_404(user_id)

    # Protect Primary Admin
    if user.email == "nor.jws@gmail.com" and current_user.email != "nor.jws@gmail.com":
        flash("The primary administrator account cannot be edited.", "danger")
        return redirect(url_for('auth.list_users'))

    # Initialize form and set role choices dynamically
    form = EditUserForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]

    if form.validate_on_submit():
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        if hasattr(form, "name"):
            user.name = form.name.data

        db.session.commit()
        log_action(f"User profile edited by {current_user.name}", object_type="User", object_id=user_id)
        flash("User updated successfully!", "success")
        return redirect(url_for('auth.list_users'))

    return render_template("auth/edit_user.html", form=form, user=user)






# Unified delete_user route supporting both JSON/AJAX and normal form
@bp.route("/user/delete/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    """Deletes a user. Only accessible to 'admin' role."""
    user = User.query.get_or_404(user_id)

    # Protect Primary Admin
    if user.email == "nor.jws@gmail.com":
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "error", "message": "The primary admin account cannot be deleted."}), 400
        flash("The primary administrator account cannot be deleted.", "danger")
        return redirect(url_for("auth.list_users"))

    # Prevent deleting own account
    if user.id == current_user.id:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "error", "message": "You cannot delete your own account."}), 400
        
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for("auth.list_users"))

    db.session.delete(user)
    db.session.commit()

    log_action("User deleted", object_type="User", object_id=user_id)

    # Response for AJAX/JSON request
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": f"User {user.name} deleted successfully"}), 200

    # Response for standard form submission
    flash(f"User {user.name} deleted successfully.", "success")
    return redirect(url_for("auth.list_users"))


# ----------------------------------
# Role & Permission Management
# ----------------------------------

@bp.route("/roles")
@login_required
@role_required("admin")
def list_roles():
    """List all roles with their permissions."""
    roles = Role.query.order_by(Role.name).all()
    return render_template("auth/roles.html", roles=roles)

@bp.route("/roles/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_role():
    """Create a new role with specific permissions."""
    form = RoleForm()
    # Populate permission choices
    form.permissions.choices = [(p.id, p.name) for p in Permission.query.order_by(Permission.name).all()]

    if form.validate_on_submit():
        if Role.query.filter_by(name=form.name.data).first():
            flash("Role already exists.", "danger")
        else:
            role = Role(name=form.name.data, description=form.description.data)
            
            # Assign permissions
            selected_perms = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
            role.permissions.extend(selected_perms)
            
            db.session.add(role)
            db.session.commit()
            flash(f"Role '{role.name}' created successfully.", "success")
            return redirect(url_for("auth.list_roles"))
            
    return render_template("auth/edit_role.html", form=form, title="Create New Role")

@bp.route("/roles/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_role(id):
    """Edit an existing role and its permissions."""
    role = Role.query.get_or_404(id)
    form = RoleForm(obj=role)
    
    # Populate choices
    form.permissions.choices = [(p.id, p.name.replace('_', ' ').title()) for p in Permission.query.order_by(Permission.name).all()]
    
    if request.method == 'GET':
        # Pre-select existing permissions
        form.permissions.data = [p.id for p in role.permissions]

    if form.validate_on_submit():
        if role.name.lower() == 'admin' and form.name.data.lower() != 'admin':
            flash("Cannot rename the 'Admin' role.", "danger")
            return redirect(url_for("auth.list_roles"))
            
        role.name = form.name.data
        role.description = form.description.data
        
        # update permissions
        role.permissions = [] # Clear current
        selected_perms = Permission.query.filter(Permission.id.in_(form.permissions.data)).all()
        role.permissions.extend(selected_perms)
        
        db.session.commit()
        flash(f"Role '{role.name}' updated successfully.", "success")
        return redirect(url_for("auth.list_roles"))
        
    return render_template("auth/edit_role.html", form=form, title="Edit Role", role=role)

@bp.route("/roles/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_role(id):
    """Delete a role (unless it's Admin or assigned to users)."""
    role = Role.query.get_or_404(id)
    
    if role.name.lower() in ['admin', 'manager', 'staff']: # Protect core roles
        flash(f"Cannot delete protected role '{role.name}'.", "danger")
        return redirect(url_for("auth.list_roles"))
        
    if role.users: # Check if users are assigned
        flash(f"Cannot delete role '{role.name}' because it is assigned to users.", "warning")
        return redirect(url_for("auth.list_roles"))
        
    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' deleted.", "success")
    return redirect(url_for("auth.list_roles"))