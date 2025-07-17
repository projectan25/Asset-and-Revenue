from flask import Blueprint, render_template
from flask_login import current_user

from models import Receipt

receipt_bp = Blueprint('receipt', __name__)

# Existing create route
@receipt_bp.route('/create')
def create():
    return render_template('receipts/create.html')

# Add this view_all route
@receipt_bp.route('/view')
def view_all():
    receipts = Receipt.query.filter_by(user_id=current_user.id).all()
    return render_template('receipts/view_all.html', receipts=receipts)