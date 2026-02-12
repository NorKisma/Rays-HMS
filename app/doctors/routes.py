from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.decorators import permission_required
from app.extensions import db
from . import bp
from app.models import Doctor
from .forms import DoctorForm

@bp.route('/')
@login_required
@permission_required('view_doctors')
def index():
    doctors = Doctor.query.filter_by(is_deleted=False).all()
    return render_template('doctors/index.html', doctors=doctors)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_doctors')
def add():
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor()
        form.populate_obj(doctor)
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor registered successfully!', 'success')
        return redirect(url_for('doctors.index'))
    return render_template('doctors/create.html', form=form, title="Register New Doctor")

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_doctors')
def edit(id):
    doctor = Doctor.query.get_or_404(id)
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        form.populate_obj(doctor)
        db.session.commit()
        flash('Doctor profile updated!', 'success')
        return redirect(url_for('doctors.index'))
    return render_template('doctors/create.html', form=form, title="Edit Doctor Profile")

@bp.route('/view/<int:id>')
@login_required
@permission_required('view_doctors')
def view(id):
    doctor = Doctor.query.get_or_404(id)
    return render_template('doctors/view.html', doctor=doctor)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('edit_doctors') # Assuming edit permission allows deletion/archiving
def delete(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.soft_delete()
    db.session.commit()
    flash('Doctor archived successfully!', 'success')
    return redirect(url_for('doctors.index'))
