from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from datetime import datetime
from models import db, Receipt
from sqlalchemy.exc import SQLAlchemyError

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
                date=datetime.utcnow()
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

@receipt_bp.route('/export_all')
@login_required
def export_all():
    try:
        # Get all receipts for current user's department
        receipts = Receipt.query.filter_by(
            depart_code=current_user.department.depart_code
        ).order_by(Receipt.date.desc()).all()
        
        # Prepare data for export
        receipts_data = []
        for receipt in receipts:
            receipts_data.append({
                'Main Head': receipt.main_heading,
                'Major Head': receipt.major_head,
                'Sub Head': receipt.sub_head,
                'Sub Ledger': receipt.sub_ledger,
                'Amount (₹)': float(receipt.amount),
                'Date': receipt.date.strftime('%Y-%m-%d')
            })
            
        return jsonify(receipts_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@receipt_bp.route('/view_all')
@login_required
def view_all():
    # Get page number from request (default to 1)
    page = request.args.get('page', 1, type=int)
    
    # Get items per page from request (default to 10)
    per_page = request.args.get('per_page', 10, type=str)
    
    # Base query
    query = Receipt.query.filter_by(
        depart_code=current_user.department.depart_code
    ).order_by(Receipt.date.desc())
    
    # Handle 'all' option
    if per_page == 'all':
        receipts = query.all()
        pagination = None
    else:
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = 10
            
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        receipts = pagination.items
    
    return render_template('receipts/view_all.html', 
                         receipts=receipts,
                         pagination=pagination,
                         per_page=per_page)

@receipt_bp.route('/view/<int:receipt_id>')
@login_required
def view(receipt_id):
    """View details of a specific receipt"""
    receipt = Receipt.query.filter_by(
        receipt_id=receipt_id,
        depart_code=current_user.department.depart_code
    ).first_or_404()
    
    return render_template('receipts/view.html', receipt=receipt)

@receipt_bp.route('/delete/<int:receipt_id>', methods=['DELETE'])
@login_required
def delete(receipt_id):
    try:
        # Verify the receipt exists and belongs to the user's department
        receipt = Receipt.query.filter_by(
            receipt_id=receipt_id,
            depart_code=current_user.department.depart_code
        ).first()

        if not receipt:
            return jsonify({
                "success": False, 
                "message": "Receipt not found or not authorized"
            }), 404

        db.session.delete(receipt)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Receipt deleted successfully"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False, 
            "message": str(e)
        }), 500