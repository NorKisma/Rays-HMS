from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from app.models.lab import LabRequest, LabResultTemplate
from . import bp

from .forms import LabResultForm

@bp.route('/')
@login_required
def index():
    # Show requests where status is 'pending'
    requests = LabRequest.query.filter_by(status='pending').order_by(LabRequest.created_at.asc()).all()
    return render_template('lab/index.html', requests=requests)

@bp.route('/completed')
@login_required
def completed():
    results = LabRequest.query.filter(LabRequest.status.in_(['completed', 'reviewed'])).order_by(LabRequest.updated_at.desc()).all()
    return render_template('lab/completed.html', results=results)

@bp.route('/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process(id):
    req = LabRequest.query.get_or_404(id)
    form = LabResultForm()
    templates = LabResultTemplate.query.filter_by(is_deleted=False).order_by(LabResultTemplate.name).all()
    
    if form.validate_on_submit():
        req.result = form.result.data
        req.status = 'completed'
        req.technician_id = current_user.id
        
        db.session.commit()
        
        pending_count = LabRequest.query.filter_by(appointment_id=req.appointment_id, status='pending').count()
        if pending_count == 0:
            req.appointment.status = 'lab_review'
            db.session.commit()
            
        flash('Results submitted. Returned to Doctor.', 'success')
        return redirect(url_for('lab.index'))
        
    return render_template('lab/process.html', form=form, request=req, templates=templates)

@bp.route('/report/<int:id>/print')
@login_required
def print_report(id):
    req = LabRequest.query.get_or_404(id)
    if req.status != 'completed':
        flash('Report is not yet completed.', 'warning')
        return redirect(url_for('lab.index'))
    return render_template('lab/print_report.html', req=req)

# ---------------------------------------------------------
# Lab Result Templates
# ---------------------------------------------------------
@bp.route('/templates')
@login_required
def list_templates():
    templates = LabResultTemplate.query.filter_by(is_deleted=False).order_by(LabResultTemplate.name).all()
    return render_template('lab/templates.html', templates=templates)

@bp.route('/templates/add', methods=['POST'])
@login_required
def add_template():
    name = request.form.get('name')
    category = request.form.get('category')
    fields_text = request.form.get('fields')
    
    template = LabResultTemplate(
        name=name,
        category=category,
        fields=fields_text
    )
    db.session.add(template)
    db.session.commit()
    flash(f'Template "{name}" created successfully.', 'success')
    return redirect(url_for('lab.list_templates'))

@bp.route('/templates/delete/<int:id>')
@login_required
def delete_template(id):
    template = LabResultTemplate.query.get_or_404(id)
    template.soft_delete()
    db.session.commit()
    flash('Template removed.', 'success')
    return redirect(url_for('lab.list_templates'))

@bp.route('/api/template/<int:id>')
@login_required
def get_template(id):
    template = LabResultTemplate.query.get_or_404(id)
    return jsonify({'name': template.name, 'fields': template.fields})
