from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Department, Receipt

# Create the Blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def user_dashboard():
    # Get user's receipts or other relevant data
    user_receipts = Receipt.query.filter_by(user_id=current_user.user_id).all()
    return render_template('user/user_dashboard.html', receipts=user_receipts)

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', user=current_user)

# Add more user routes as needed