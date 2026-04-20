import os
from sqlalchemy import inspect, text
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.saas import saas_bp
from app.models import Hospital, db
from app.decorators import role_required
from functools import wraps

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name.lower() != 'developer':
            flash("Keliya Developer ayaa geli kara qaybtan.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@saas_bp.route('/hospitals')
@login_required
@super_admin_required
def list_hospitals():
    hospitals = Hospital.query.all()
    
    # Calculate simple stats for tiles
    stats = {
        'total': len(hospitals),
        'active': len([h for h in hospitals if h.subscription_status == 'active']),
        'pro': len([h for h in hospitals if h.plan == 'professional']),
        'ent': len([h for h in hospitals if h.plan == 'enterprise'])
    }
    
    return render_template('saas/hospitals.html', hospitals=hospitals, stats=stats)

@saas_bp.route('/hospitals/new', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_hospital():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug').lower().replace(' ', '-')
        plan = request.form.get('plan')
        
        # User details for the first admin
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        admin_pass = request.form.get('admin_password')
        
        from app.models import User, Role, db
        import bcrypt
        
        # 1. Create Hospital
        hospital = Hospital(name=name, slug=slug, plan=plan)
        hospital.has_pos = 'has_pos' in request.form
        hospital.has_pharmacy = 'has_pharmacy' in request.form
        hospital.has_clinical = 'has_clinical' in request.form
        hospital.has_accounting = 'has_accounting' in request.form
        hospital.has_lab = 'has_lab' in request.form
        hospital.has_inventory = 'has_inventory' in request.form
        hospital.has_ipd = 'has_ipd' in request.form
        
        db.session.add(hospital)
        db.session.flush() # Get the hospital ID
        
        # 2. Create Admin User for this hospital
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
             admin_role = Role(name='Admin')
             db.session.add(admin_role)
             db.session.flush()
        
        hashed_password = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_admin = User(
            name=admin_name,
            email=admin_email,
            password_hash=hashed_password,
            role_id=admin_role.id,
            hospital_id=hospital.id,
            is_active=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash(f"Hospital '{name}' and Admin account '{admin_email}' created successfully!", "success")
        return redirect(url_for('saas.list_hospitals'))
    
    return render_template('saas/hospital_form.html')

@saas_bp.route('/hospitals/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_hospital(id):
    hospital = Hospital.query.get_or_404(id)
    if request.method == 'POST':
        hospital.name = request.form.get('name')
        hospital.plan = request.form.get('plan')
        hospital.subscription_status = request.form.get('status')
        
        hospital.has_pos = 'has_pos' in request.form
        hospital.has_pharmacy = 'has_pharmacy' in request.form
        hospital.has_clinical = 'has_clinical' in request.form
        hospital.has_accounting = 'has_accounting' in request.form
        hospital.has_lab = 'has_lab' in request.form
        hospital.has_inventory = 'has_inventory' in request.form
        hospital.has_ipd = 'has_ipd' in request.form
        
        db.session.commit()
        flash(f"Hospital '{hospital.name}' updated successfully!", "success")
        return redirect(url_for('saas.list_hospitals'))
    
    return render_template('saas/hospital_form.html', hospital=hospital)

# ----------------------------------
# Developer Console Features
# ----------------------------------

@saas_bp.route('/logs')
@login_required
@super_admin_required
def system_logs():
    log_path = 'app_start.log'
    logs = "No log file found."
    if os.path.exists(log_path):
        # Using latin-1 or utf-8 with errors='replace' to avoid UnicodeDecodeError on Windows
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            # Get last 200 lines
            try:
                lines = f.readlines()
                logs = "".join(lines[-200:])
            except Exception as e:
                logs = f"Error reading logs: {str(e)}"
    return render_template('saas/logs.html', logs=logs)

@saas_bp.route('/schema')
@login_required
@super_admin_required
def schema_explorer():
    target_table = request.args.get('table')
    inspector = inspect(db.engine)

    if target_table:
        # Detailed table view
        columns = []
        try:
            pk_constraint = inspector.get_pk_constraint(target_table) or {}
            pk_columns = set(pk_constraint.get('constrained_columns') or [])
            foreign_keys = inspector.get_foreign_keys(target_table) or []
            fk_columns = {fk['constrained_columns'][0]: fk for fk in foreign_keys if fk.get('constrained_columns')}

            for col in inspector.get_columns(target_table):
                default_val = col.get('default')
                if default_val is None:
                    default_val = col.get('server_default')
                extra = ''
                if col.get('autoincrement') in (True, 'auto', 'auto_increment'):
                    extra = 'AUTOINCREMENT'

                columns.append({
                    'field': col['name'],
                    'type': str(col['type']),
                    'null': 'YES' if col.get('nullable', True) else 'NO',
                    'key': 'PRI' if col['name'] in pk_columns else ('MUL' if col['name'] in fk_columns else ''),
                    'default': default_val,
                    'extra': extra
                })
        except Exception as e:
            flash(f"Error describing table: {str(e)}", "danger")
        return render_template('saas/table_view.html', table_name=target_table, columns=columns)

    tables = []
    try:
        preparer = db.engine.dialect.identifier_preparer
        for table_name in sorted(inspector.get_table_names()):
            try:
                quoted_table = preparer.quote(table_name)
                count_res = db.session.execute(text(f"SELECT COUNT(*) FROM {quoted_table}")).scalar()
            except Exception:
                count_res = 0
            tables.append({'name': table_name, 'count': count_res})
    except Exception as e:
        flash(f"Schema Error: {str(e)}", "danger")
    return render_template('saas/schema.html', tables=tables)

@saas_bp.route('/api-map')
@login_required
@super_admin_required
def api_management():
    from flask import current_app
    from collections import defaultdict
    
    # Group routes by blueprint
    blueprints = defaultdict(list)
    stats = {
        'total': 0,
        'get': 0,
        'post': 0,
        'other': 0
    }
    
    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint
        bp_name = endpoint.split('.')[0] if '.' in endpoint else 'Global'
        
        methods = [m for m in rule.methods if m not in ['OPTIONS', 'HEAD']]
        
        route_info = {
            'endpoint': endpoint,
            'methods': methods,
            'path': str(rule),
            'doc': current_app.view_functions[endpoint].__doc__ or "No documentation provided."
        }
        
        blueprints[bp_name].append(route_info)
        
        # Stats
        stats['total'] += 1
        if 'GET' in methods: stats['get'] += 1
        if 'POST' in methods: stats['post'] += 1
        if any(m in methods for m in ['PUT', 'DELETE', 'PATCH']): stats['other'] += 1

    return render_template('saas/api_map.html', blueprints=dict(blueprints), stats=stats)

@saas_bp.route('/audit-log')
@login_required
@super_admin_required
def audit_log():
    from app.models import LogAction
    # Query logs related to SaaS operations
    logs = LogAction.query.order_by(LogAction.created_at.desc()).limit(100).all()
    return render_template('saas/audit_log.html', logs=logs)

@saas_bp.route('/hospitals/toggle-status/<int:id>', methods=['POST'])
@login_required
@super_admin_required
def toggle_hospital_status(id):
    hospital = Hospital.query.get_or_404(id)
    if hospital.subscription_status == 'active':
        hospital.subscription_status = 'suspended'
    else:
        hospital.subscription_status = 'active'
    db.session.commit()
    flash(f"Status for '{hospital.name}' updated to {hospital.subscription_status}.", "info")
    return redirect(url_for('saas.list_hospitals'))

@saas_bp.route('/hospitals/impersonate/<int:id>')
@login_required
@super_admin_required
def impersonate(id):
    from flask_login import login_user
    from app.models import User
    
    # Check if hospital exists
    hospital = Hospital.query.get_or_404(id)
    
    # Find the first admin of that hospital
    admin_user = User.query.filter_by(hospital_id=id).first()
    
    if not admin_user:
        flash(f"No administrative user found for {hospital.name}.", "warning")
        return redirect(url_for('saas.list_hospitals'))
        
    # Log in as that user
    login_user(admin_user)
    flash(f"You are now impersonating {admin_user.name} @ {hospital.name}.", "success")
    return redirect(url_for('main.dashboard'))
