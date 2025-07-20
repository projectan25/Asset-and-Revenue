from flask import Blueprint, jsonify, render_template, request
from models import db
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from datetime import datetime
from models import Receipt

receipt_bp = Blueprint('receipt', __name__)



@receipt_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['main_heading', 'major_head', 'sub_head', 'sub_ledger', 'amount']
            if not all(field in data for field in required_fields):
                return jsonify({"success": False, "message": "Missing required fields"}), 400
            
            # Create receipt with proper datetime
            new_receipt = Receipt(
                user_id=current_user.id,
                depart_code=current_user.department.depart_code,
                main_heading=data['main_heading'],
                major_head=data['major_head'],
                sub_head=data['sub_head'],
                sub_ledger=data['sub_ledger'],
                amount=float(data['amount']),
                date=datetime.utcnow()  # Correct usage
            )
            
            db.session.add(new_receipt)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Receipt created successfully",
                "receipt_id": new_receipt.receipt_id
            })
            
        except ValueError:
            db.session.rollback()
            return jsonify({"success": False, "message": "Invalid amount format"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
    
    return render_template('receipts/create.html')


@receipt_bp.route('/view_all')
@login_required
def view_all():
    # Filter receipts by the current user's department code
    receipts = Receipt.query.filter_by(depart_code=current_user.department.depart_code).all()
    return render_template('receipts/view_all.html', receipts=receipts)

@receipt_bp.route('/view/<int:receipt_id>')
@login_required
def view(receipt_id):
    # Get receipt and verify it belongs to user's department
    receipt = Receipt.query.filter_by(
        receipt_id=receipt_id,
        depart_code=current_user.department.depart_code
    ).first_or_404()
    
    return render_template('receipts/view.html', receipt=receipt)