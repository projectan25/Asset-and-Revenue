from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Department
from functools import wraps

admin_department_bp = Blueprint('admin_department', __name__, url_prefix='/admin/departments')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_global_admin:
            flash('Access denied: Admin privileges required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_department_bp.route('/')
@login_required
@admin_required
def manage_departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_department_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_department():
    depart_code = request.form.get('depart_code')
    depart_name = request.form.get('depart_name')
    
    if Department.query.filter_by(depart_code=depart_code).first():
        flash('Department code already exists', 'danger')
        return redirect(url_for('admin_department.manage_departments'))
    
    new_dept = Department(
        depart_code=depart_code,
        depart_name=depart_name
    )
    
    db.session.add(new_dept)
    db.session.commit()
    flash('Department created successfully', 'success')
    return redirect(url_for('admin_department.manage_departments'))

@admin_department_bp.route('/<string:depart_code>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(depart_code):
    department = Department.query.get_or_404(depart_code)
    
    # Check if department has users
    if department.users:
        flash('Cannot delete department with assigned users', 'danger')
    else:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully', 'success')
    
    return redirect(url_for('admin_department.manage_departments'))

@admin_department_bp.route('/api')
@login_required
@admin_required
def api_departments():
    departments = Department.query.all()
    return jsonify([{
        'code': dept.depart_code,
        'name': dept.depart_name,
        'user_count': len(dept.users)
    } for dept in departments])