from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User, Department, Receipt
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def user_dashboard():
    # Get user's department receipts with pagination
    page = request.args.get('page', 1, type=int)
    receipts = Receipt.query.filter_by(depart_code=current_user.depart_code)\
                           .order_by(Receipt.date.desc())\
                           .paginate(page=page, per_page=10)
    
    # Calculate department totals
    total_amount = db.session.query(db.func.sum(Receipt.amount))\
                            .filter_by(depart_code=current_user.depart_code)\
                            .scalar() or 0
    
    return render_template('user/dashboard.html', 
                         receipts=receipts,
                         total_amount=total_amount,
                         department=current_user.department)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        changes_made = False
        
        # Username update
        if username and username != current_user.username:
            if User.query.filter(User.username == username, User.id != current_user.id).first():
                flash('Username already taken', 'danger')
            else:
                current_user.username = username
                changes_made = True
                flash('Username updated successfully', 'success')
        
        # Password change
        if current_password or new_password or confirm_password:
            if not all([current_password, new_password, confirm_password]):
                flash('Please fill all password fields', 'danger')
            elif not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            elif len(new_password) < 8:
                flash('Password must be at least 8 characters', 'danger')
            else:
                current_user.password_hash = generate_password_hash(new_password)
                changes_made = True
                flash('Password changed successfully!', 'success')
        
        if changes_made:
            db.session.commit()
        
        return redirect(url_for('user.profile'))
    
    return render_template('user/profile.html', user=current_user)