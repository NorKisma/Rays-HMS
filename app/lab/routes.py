from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from app.models.lab import LabRequest
from . import bp

from .forms import LabResultForm

@bp.route('/')
@login_required
def index():
    # Show requests where status is 'pending'
    requests = LabRequest.query.filter_by(status='pending').order_by(LabRequest.created_at.asc()).all()
    return render_template('lab/index.html', requests=requests)

@bp.route('/process/<int:id>', methods=['GET', 'POST'])
@login_required
def process(id):
    req = LabRequest.query.get_or_404(id)
    form = LabResultForm()
    
    if form.validate_on_submit():
        req.result = form.result.data
        req.status = 'completed'
        req.technician_id = current_user.id
        
        db.session.commit() # Commit first to save req update
        
        # Check if all requests for this appointment are done
        # We need to query again to be sure or check logic
        # Count pending requests for this appointment EXCLUDING this one (which is now completed)
        # Actually since we committed, this one is completed. So check if ANY pending left.
        
        pending_count = LabRequest.query.filter_by(appointment_id=req.appointment_id, status='pending').count()
        if pending_count == 0:
            req.appointment.status = 'lab_review'
            db.session.commit()
            
        flash('Results submitted. Returned to Doctor.', 'success')
        return redirect(url_for('lab.index'))
        
    return render_template('lab/process.html', form=form, request=req)
