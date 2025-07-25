from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import re
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = 'departments'
    depart_code = db.Column(db.String(20), primary_key=True)
    depart_name = db.Column(db.String(100), nullable=False)

# models.py
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_role = db.Column(db.String(20), default='user')
    is_global_admin = db.Column(db.Boolean, default=False)
    depart_code = db.Column(db.String(10), db.ForeignKey('departments.depart_code'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department = db.relationship('Department', backref='users')
    
    def __repr__(self):
        return f'<User {self.username}>'
    


# Main Heading Model (e.g., "Student Fee", "Others")
class MainHeading(db.Model):
    __tablename__ = 'main_headings'
    main_heading_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "Student Fee", "Others"

    def __repr__(self):
        return f'<MainHeading {self.name}>'

# Major Head Model (e.g., "Academic Fee", "Research" under "Student Fee")
class MajorHead(db.Model):
    __tablename__ = 'major_heads'
    major_head_id = db.Column(db.Integer, primary_key=True)
    main_heading_id = db.Column(db.Integer, db.ForeignKey('main_headings.main_heading_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Academic Fee", "Research"

    main_heading = db.relationship('MainHeading', backref=db.backref('major_heads', lazy=True))

    def __repr__(self):
        return f'<MajorHead {self.name}>'

# Sub Head Model (e.g., subcategories under "Academic Fee")
class SubHead(db.Model):
    __tablename__ = 'sub_heads'
    sub_head_id = db.Column(db.Integer, primary_key=True)
    major_head_id = db.Column(db.Integer, db.ForeignKey('major_heads.major_head_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    major_head = db.relationship('MajorHead', backref=db.backref('sub_heads', lazy=True))

    def __repr__(self):
        return f'<SubHead {self.name}>'

# Sub Ledger Model (e.g., specific ledgers under a Sub Head)
class SubLedger(db.Model):
    __tablename__ = 'sub_ledgers'
    sub_ledger_id = db.Column(db.Integer, primary_key=True)
    sub_head_id = db.Column(db.Integer, db.ForeignKey('sub_heads.sub_head_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    sub_head = db.relationship('SubHead', backref=db.backref('sub_ledgers', lazy=True))

    def __repr__(self):
        return f'<SubLedger {self.name}>'



#Receipt Model with all relationships
class Receipt(db.Model):
    __tablename__ = 'receipts'
    receipt_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    depart_code = db.Column(db.String(20), db.ForeignKey('departments.depart_code'), nullable=False)
    
    # Category fields as strings
    main_heading = db.Column(db.String(100), nullable=False)
    major_head = db.Column(db.String(100), nullable=False)
    sub_head = db.Column(db.String(100), nullable=False)
    sub_ledger = db.Column(db.String(100), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (only for user and department)
    user = db.relationship('User', backref=db.backref('receipts', lazy=True))
    department = db.relationship('Department', backref=db.backref('receipts', lazy=True))

    def __repr__(self):
        return f'<Receipt {self.receipt_id} by User {self.user_id}>'



