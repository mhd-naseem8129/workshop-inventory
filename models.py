from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------- User Model ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# ---------- Spare Model ----------
class Spare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sales = db.relationship('Sale', backref='spare', lazy=True)

# ---------- Sale Model ----------
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spare_id = db.Column(db.Integer, db.ForeignKey('spare.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Employee Model ----------
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    aadhaar = db.Column(db.String(20), nullable=False)
    aadhaar_file = db.Column(db.String(200), nullable=True)
    joining_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
