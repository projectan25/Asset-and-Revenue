from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/', methods=['GET'])
def index():
    return render_template('login.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user in database
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user.password_hash, password):
            # Log the user in
            login_user(user)
            
            # Redirect based on role
            if user.user_role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('user.user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    # For GET requests or failed login
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# Example of a protected route that checks user role
@auth_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    else:
        return redirect(url_for('user.user_dashboard'))

# API endpoint for login (if you need JSON responses)
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': '/admin/dashboard' if user.user_role == 'admin' else '/user/dashboard'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401