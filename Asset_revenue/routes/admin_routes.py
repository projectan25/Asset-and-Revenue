from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Department
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

############################## Admin Dashboard ###############################################################

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

############################### User Management ###############################################################

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

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username.asc()).paginate(page=page, per_page=10)
    departments = Department.query.all()
    return render_template('admin/users.html', users=users, departments=departments)


############################## Department Management###############################################################



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


@admin_bp.route('/api/departments/<string:depart_code>')
@login_required
@admin_required
def api_department(depart_code):
    try:
        department = Department.query.get_or_404(depart_code)
        return jsonify({
            'code': department.depart_code,
            'name': department.depart_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/departments/<string:depart_code>/edit', methods=['POST'])
@login_required
@admin_required
def edit_department(depart_code):
    # Get form data
    data = request.get_json() if request.is_json else request.form
    new_code = data.get('depart_code')
    new_name = data.get('depart_name')
    
    # Validate required fields
    if not new_name or not new_code:
        return jsonify({
            'success': False,
            'message': 'Both department code and name are required'
        }), 400
    
    # Get the existing department
    department = Department.query.get_or_404(depart_code)
    
    # Check if new code already exists (if it's being changed)
    if new_code != depart_code:
        if Department.query.filter_by(depart_code=new_code).first():
            return jsonify({
                'success': False,
                'message': 'Department code already exists'
            }), 400
    
    # Check if name already exists (if it's being changed)
    if new_name != department.depart_name:
        if Department.query.filter(Department.depart_name == new_name).first():
            return jsonify({
                'success': False,
                'message': 'Department name already exists'
            }), 400
    
    # Update the department
    department.depart_code = new_code
    department.depart_name = new_name
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Department updated successfully',
            'department': {
                'code': department.depart_code,
                'name': department.depart_name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error updating department',
            'error': str(e)
        }), 500

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