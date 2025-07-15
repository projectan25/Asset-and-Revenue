from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Department

# Create the department Blueprint
depart_bp = Blueprint('depart', __name__)

@depart_bp.route('/departments')
@login_required
def list_departments():
    if current_user.user_role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('user.user_dashboard'))
    
    departments = Department.query.all()
    return render_template('departments/list.html', departments=departments)

