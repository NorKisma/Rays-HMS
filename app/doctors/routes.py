from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from . import bp
from app.models import Doctor
from .forms import DoctorForm

@bp.route('/')
@login_required
@permission_required('view_doctors')
def index():
    doctors = Doctor.query.filter_by(is_deleted=False, hospital_id=current_user.hospital_id).all()
    return render_template('doctors/index.html', doctors=doctors)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_doctors')
def add():
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor()
        form.populate_obj(doctor)
        doctor.hospital_id = current_user.hospital_id
        db.session.add(doctor)
        db.session.commit()
        flash('Staff registered successfully!', 'success')
        return redirect(url_for('doctors.index'))
    return render_template('doctors/create.html', form=form, title="Register New Staff")

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('edit_doctors')
def edit(id):
    doctor = Doctor.query.filter_by(id=id, hospital_id=current_user.hospital_id).first_or_404()
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        form.populate_obj(doctor)
        db.session.commit()
        flash('Staff profile updated!', 'success')
        return redirect(url_for('doctors.index'))
    return render_template('doctors/create.html', form=form, title="Edit Staff Profile")

@bp.route('/view/<int:id>')
@login_required
@permission_required('view_doctors')
def view(id):
    doctor = Doctor.query.filter_by(id=id, hospital_id=current_user.hospital_id).first_or_404()
    return render_template('doctors/view.html', doctor=doctor)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('edit_doctors') # Assuming edit permission allows deletion/archiving
def delete(id):
    doctor = Doctor.query.filter_by(id=id, hospital_id=current_user.hospital_id).first_or_404()
    doctor.soft_delete()
    db.session.commit()
    flash('Staff record archived successfully!', 'success')
    return redirect(url_for('doctors.index'))
