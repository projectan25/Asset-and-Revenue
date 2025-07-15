from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from models import User, Department
from functools import wraps

admin_dashboard_bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_global_admin:
            flash('Access denied: Admin privileges required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_dashboard_bp.route('/dashboard')
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