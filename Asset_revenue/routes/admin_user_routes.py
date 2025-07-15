from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Department
from werkzeug.security import generate_password_hash
from functools import wraps

admin_user_bp = Blueprint('admin_user', __name__, url_prefix='/admin/users')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_global_admin:
            flash('Access denied: Admin privileges required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_user_bp.route('/')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.order_by(Department.depart_name).all()
    return render_template('admin/users.html', 
                         users=users, 
                         departments=departments)

@admin_user_bp.route('/create', methods=['POST'])
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
        return redirect(url_for('admin_user.manage_users'))
    
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
    return redirect(url_for('admin_user.manage_users'))

@admin_user_bp.route('/<int:user_id>/toggle-admin', methods=['POST'])
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
    return redirect(url_for('admin_user.manage_users'))

@admin_user_bp.route('/<int:user_id>/delete', methods=['POST'])
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
    return redirect(url_for('admin_user.manage_users'))

@admin_user_bp.route('/api')
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