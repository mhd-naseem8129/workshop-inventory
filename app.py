from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from models import db, User, Spare, Sale, Employee

# ---------- App Initialization ----------
app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload config
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Init DB
db.init_app(app)

# ---------- Login Setup ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Routes ----------

# --- Login ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials', 'danger')
    return render_template('login.html')

# --- Dashboard ---
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# --- Inventory ---
@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        new_spare = Spare(name=name, company=company, quantity=quantity, price=price)
        db.session.add(new_spare)
        db.session.commit()
        flash('Spare added successfully!', 'success')
        return redirect(url_for('inventory'))

    spares = Spare.query.all()
    return render_template('inventory.html', spares=spares)

@app.route('/edit-spare/<int:spare_id>', methods=['GET', 'POST'])
@login_required
def edit_spare(spare_id):
    spare = Spare.query.get_or_404(spare_id)
    if request.method == 'POST':
        spare.name = request.form['name']
        spare.company = request.form['company']
        spare.quantity = int(request.form['quantity'])
        spare.price = float(request.form['price'])

        db.session.commit()
        flash('Spare updated successfully!', 'success')
        return redirect(url_for('inventory'))

    return render_template('edit_spare.html', spare=spare)

@app.route('/delete-spare/<int:spare_id>')
@login_required
def delete_spare(spare_id):
    spare = Spare.query.get(spare_id)
    if spare:
        db.session.delete(spare)
        db.session.commit()
        flash('Spare deleted!', 'danger')
    return redirect(url_for('inventory'))

# --- Sales Tracker ---
@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    spares = Spare.query.all()

    if request.method == 'POST':
        spare_id = int(request.form['spare_id'])
        quantity_sold = int(request.form['quantity'])

        spare = Spare.query.get(spare_id)
        if spare and spare.quantity >= quantity_sold:
            spare.quantity -= quantity_sold
            new_sale = Sale(spare_id=spare.id, quantity_sold=quantity_sold)
            db.session.add(new_sale)
            db.session.commit()
            flash('Sale recorded and stock updated!', 'success')
        else:
            flash('Not enough stock to complete sale.', 'danger')

        return redirect(url_for('sales'))

    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sales.html', spares=spares, sales=sales)

# --- Employee Management ---
@app.route('/employees')
@login_required
def view_employees():
    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/add-employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        designation = request.form['designation']
        contact = request.form['contact']
        aadhaar = request.form['aadhaar']
        joining_date = request.form['joining_date']

        image = request.files['aadhaar_image']
        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

        new_emp = Employee(
            name=name,
            designation=designation,
            contact=contact,
            aadhaar=aadhaar,
            joining_date=datetime.strptime(joining_date, '%Y-%m-%d'),
            aadhaar_image=filename
        )
        db.session.add(new_emp)
        db.session.commit()
        flash("Employee added successfully!", "success")
        return redirect(url_for('view_employees'))

    return render_template('add_employee.html')

@app.route('/edit-employee/<int:emp_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)

    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        emp.name = request.form['name']
        emp.designation = request.form['designation']
        emp.contact = request.form['contact']
        emp.aadhaar = request.form['aadhaar']
        db.session.commit()
        flash("Employee updated!", "success")
        return redirect(url_for('view_employees'))

    return render_template('edit_employee.html', employee=emp)

@app.route('/delete-employee/<int:emp_id>')
@login_required
def delete_employee(emp_id):
    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    flash("Employee deleted.", "danger")
    return redirect(url_for('view_employees'))

# --- Manage Staff ---
@app.route('/manage-staff')
@login_required
def manage_staff():
    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('manage_staff.html', users=users)

@app.route('/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied. Admins only!", "danger")
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("You can't delete an admin!", "warning")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Staff user deleted successfully!", "success")

    return redirect(url_for('manage_staff'))

# --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- DB Setup ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
            staff = User(username='staff', password=generate_password_hash('staff123'), role='staff')
            db.session.add_all([admin, staff])
            db.session.commit()

    app.run(debug=True)
