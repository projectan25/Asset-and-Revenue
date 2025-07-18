from flask import Blueprint, render_template, request, jsonify
from models import db, MainHeading, MajorHead, SubHead, SubLedger

accounting_bp = Blueprint('accounting', __name__, url_prefix='/api/accounting')




@accounting_bp.route('/hierarchy')
def accounting_hierarchy():
    return render_template('admin/accounting_hierarchy.html')  

@accounting_bp.route('/main_headings', methods=['GET', 'POST'])
def main_headings():
    if request.method == 'GET':
        headings = MainHeading.query.all()
        return jsonify([{'id': h.main_heading_id, 'name': h.name} for h in headings])
    elif request.method == 'POST':
        data = request.get_json()
        new_heading = MainHeading(name=data['name'])
        db.session.add(new_heading)
        db.session.commit()
        return jsonify({'message': 'Main heading created successfully', 'id': new_heading.main_heading_id}), 201

@accounting_bp.route('/main_headings/<int:id>', methods=['PUT', 'DELETE'])
def main_heading(id):
    heading = MainHeading.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.get_json()
        heading.name = data['name']
        db.session.commit()
        return jsonify({'message': 'Main heading updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(heading)
        db.session.commit()
        return jsonify({'message': 'Main heading deleted successfully'})

# MajorHead APIs
@accounting_bp.route('/major_heads', methods=['GET', 'POST'])
def major_heads():
    if request.method == 'GET':
        heads = MajorHead.query.all()
        return jsonify([{
            'id': h.major_head_id, 
            'name': h.name,
            'main_heading_id': h.main_heading_id
        } for h in heads])
    elif request.method == 'POST':
        data = request.get_json()
        new_head = MajorHead(name=data['name'], main_heading_id=data['main_heading_id'])
        db.session.add(new_head)
        db.session.commit()
        return jsonify({'message': 'Major head created successfully', 'id': new_head.major_head_id}), 201

@accounting_bp.route('/major_heads/<int:id>', methods=['PUT', 'DELETE'])
def major_head(id):
    head = MajorHead.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.get_json()
        head.name = data['name']
        head.main_heading_id = data['main_heading_id']
        db.session.commit()
        return jsonify({'message': 'Major head updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(head)
        db.session.commit()
        return jsonify({'message': 'Major head deleted successfully'})

# SubHead APIs
@accounting_bp.route('/sub_heads', methods=['GET', 'POST'])
def sub_heads():
    if request.method == 'GET':
        heads = SubHead.query.all()
        return jsonify([{
            'id': h.sub_head_id, 
            'name': h.name,
            'major_head_id': h.major_head_id
        } for h in heads])
    elif request.method == 'POST':
        data = request.get_json()
        new_head = SubHead(name=data['name'], major_head_id=data['major_head_id'])
        db.session.add(new_head)
        db.session.commit()
        return jsonify({'message': 'Sub head created successfully', 'id': new_head.sub_head_id}), 201

@accounting_bp.route('/sub_heads/<int:id>', methods=['PUT', 'DELETE'])
def sub_head(id):
    head = SubHead.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.get_json()
        head.name = data['name']
        head.major_head_id = data['major_head_id']
        db.session.commit()
        return jsonify({'message': 'Sub head updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(head)
        db.session.commit()
        return jsonify({'message': 'Sub head deleted successfully'})

# SubLedger APIs
@accounting_bp.route('/sub_ledgers', methods=['GET', 'POST'])
def sub_ledgers():
    if request.method == 'GET':
        ledgers = SubLedger.query.all()
        return jsonify([{
            'id': l.sub_ledger_id, 
            'name': l.name,
            'sub_head_id': l.sub_head_id
        } for l in ledgers])
    elif request.method == 'POST':
        data = request.get_json()
        new_ledger = SubLedger(name=data['name'], sub_head_id=data['sub_head_id'])
        db.session.add(new_ledger)
        db.session.commit()
        return jsonify({'message': 'Sub ledger created successfully', 'id': new_ledger.sub_ledger_id}), 201

@accounting_bp.route('/sub_ledgers/<int:id>', methods=['PUT', 'DELETE'])
def sub_ledger(id):
    ledger = SubLedger.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.get_json()
        ledger.name = data['name']
        ledger.sub_head_id = data['sub_head_id']
        db.session.commit()
        return jsonify({'message': 'Sub ledger updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(ledger)
        db.session.commit()
        return jsonify({'message': 'Sub ledger deleted successfully'})