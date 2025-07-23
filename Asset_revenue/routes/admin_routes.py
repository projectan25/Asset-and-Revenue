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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Username already exists'}), 400
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
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'redirect': url_for('admin.manage_users')})
    
    flash('User created successfully', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Cannot modify your own admin status'}), 400
        flash('Cannot modify your own admin status', 'danger')
    else:
        user.is_global_admin = not user.is_global_admin
        user.user_role = 'admin' if user.is_global_admin else 'user'
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'is_admin': user.is_global_admin,
                'redirect': url_for('admin.manage_users')
            })
        flash(f'Admin status {"granted" if user.is_global_admin else "revoked"}', 'success')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/receipts/count')
@login_required
@admin_required
def count_user_receipts(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'count': len(user.receipts)
    })

@admin_bp.route('/users/<int:user_id>/reassign-receipts', methods=['POST'])
@login_required
@admin_required
def reassign_receipts(user_id):
    try:
        data = request.get_json()
        new_user_id = data.get('new_user_id')
        
        if not new_user_id:
            return jsonify({'error': 'New user ID is required'}), 400
            
        user_to_delete = User.query.get_or_404(user_id)
        new_user = User.query.get_or_404(new_user_id)
        
        if user_to_delete == new_user:
            return jsonify({'error': 'Cannot reassign to the same user'}), 400
        
        # Reassign all receipts
        for receipt in user_to_delete.receipts:
            receipt.user_id = new_user_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'All receipts reassigned to {new_user.username}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/department-check')
@login_required
@admin_required
def check_user_department(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'has_department': user.depart_code is not None,
        'receipt_count': len(user.receipts)
    })

@admin_bp.route('/api/departments')
@login_required
@admin_required
def get_departments_for_reassign():
    departments = Department.query.order_by(Department.depart_name).all()
    return jsonify([{
        'depart_code': dept.depart_code,
        'depart_name': dept.depart_name
    } for dept in departments])

@admin_bp.route('/users/<int:user_id>/update-department', methods=['POST'])
@login_required
@admin_required
def update_user_department(user_id):
    try:
        data = request.get_json()
        depart_code = data.get('depart_code')
        
        if not depart_code:
            return jsonify({'error': 'Department code is required'}), 400
            
        user = User.query.get_or_404(user_id)
        department = Department.query.get(depart_code)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        user.depart_code = depart_code
        db.session.commit()
        
        return jsonify({
            'success': True,
            'department_name': department.depart_name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user == current_user:
            return jsonify({
                'error': 'Cannot delete your own account',
                'success': False
            }), 400
            
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@admin_bp.route('/api/users')
@login_required
@admin_required
def get_users_for_reassign():
    users = User.query.order_by(User.username).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users])

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').strip()
    
    # Base query
    query = User.query
    
    # Apply search filter if search term exists
    if search_term:
        query = query.filter(
            (User.username.ilike(f'%{search_term}%')) |
            (User.email.ilike(f'%{search_term}%')) |
            (User.department.has(depart_name=search_term)))
    
    # Order and paginate
    users = query.order_by(User.username.asc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    departments = Department.query.all()
    return render_template('admin/users.html', 
                         users=users, 
                         departments=departments,
                         search_term=search_term)

@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    departments = Department.query.all()
    
    return jsonify({
        'username': user.username,
        'email': user.email,
        'depart_code': user.depart_code,
        'is_global_admin': user.is_global_admin,
        'is_active': user.is_active,
        'departments': [{
            'depart_code': dept.depart_code,
            'depart_name': dept.depart_name
        } for dept in departments]
    })

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    email = request.form.get('email')
    depart_code = request.form.get('depart_code')
    is_admin = request.form.get('is_admin') == 'on'
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Check if username already exists (excluding current user)
    if User.query.filter(User.username == username, User.id != user.id).first():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Username already exists'}), 400
        flash('Username already exists', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Check if email already exists (excluding current user)
    if User.query.filter(User.email == email, User.id != user.id).first():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Email already exists'}), 400
        flash('Email already exists', 'danger')
        return redirect(url_for('admin.manage_users'))

    # Update password if provided
    if new_password:
        if len(new_password) < 8:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Password must be at least 8 characters'}), 400
            flash('Password must be at least 8 characters', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        if new_password != confirm_password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Passwords do not match'}), 400
            flash('Passwords do not match', 'danger')
            return redirect(url_for('admin.manage_users'))
        
        user.password_hash = generate_password_hash(new_password)

    # Update other fields
    user.username = username
    user.email = email
    user.depart_code = depart_code
    user.is_global_admin = is_admin
    user.user_role = 'admin' if is_admin else 'user'

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'redirect': url_for('admin.manage_users')
        })
    
    flash('User updated successfully', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/api/users/<int:user_id>/current-department')
@login_required
@admin_required
def get_current_user_department(user_id):
    user = User.query.get_or_404(user_id)
    if not user.depart_code:
        return jsonify({'error': 'User has no department assigned'}), 404
    
    department = Department.query.get(user.depart_code)
    return jsonify({
        'depart_code': department.depart_code,
        'depart_name': department.depart_name
    })

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


@admin_bp.route('/departments/<string:depart_code>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(depart_code):
    department = Department.query.get_or_404(depart_code)
    
    # Check if department has users
    if department.users:
        return jsonify({
            'success': False,
            'message': 'Cannot delete department with assigned users'
        }), 400
    
    try:
        db.session.delete(department)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Department deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error deleting department',
            'error': str(e)
        }), 500