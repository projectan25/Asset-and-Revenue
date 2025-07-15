from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Department
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_global_admin:
            flash('Access denied: Admin privileges required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_departments = Department.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_departments=total_departments,
                         recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()
    return render_template('admin/users.html', users=users, departments=departments)

@admin_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    depart_code = request.form.get('depart_code')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    new_user = User(
        username=username,
        email=email,
        user_role='admin' if is_admin else 'user',
        depart_code=depart_code,
        is_global_admin=is_admin,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(new_user)
    db.session.commit()
    flash('User created successfully', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Cannot modify your own admin status', 'danger')
    else:
        user.is_global_admin = not user.is_global_admin
        user.user_role = 'admin' if user.is_global_admin else 'user'
        db.session.commit()
        flash(f'Admin status {"granted" if user.is_global_admin else "revoked"}', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Cannot delete your own account', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/departments')
@login_required
@admin_required
def manage_departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments/create', methods=['POST'])
@login_required
@admin_required
def create_department():
    depart_code = request.form.get('depart_code')
    depart_name = request.form.get('depart_name')
    
    if Department.query.filter_by(depart_code=depart_code).first():
        flash('Department code already exists', 'danger')
        return redirect(url_for('admin.manage_departments'))
    
    new_dept = Department(
        depart_code=depart_code,
        depart_name=depart_name
    )
    
    db.session.add(new_dept)
    db.session.commit()
    flash('Department created successfully', 'success')
    return redirect(url_for('admin.manage_departments'))

@admin_bp.route('/departments/<string:depart_code>/delete', methods=['POST'])
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
    
    return redirect(url_for('admin.manage_departments'))

# API Endpoints
@admin_bp.route('/api/users')
@login_required
@admin_required
def api_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.user_role,
        'is_admin': user.is_global_admin,
        'department': user.depart_code,
        'created_at': user.created_at.isoformat()
    } for user in users])

@admin_bp.route('/api/departments')
@login_required
@admin_required
def api_departments():
    departments = Department.query.all()
    return jsonify([{
        'code': dept.depart_code,
        'name': dept.depart_name,
        'user_count': len(dept.users)
    } for dept in departments])