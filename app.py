from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
from datetime import datetime

app = Flask(__name__)

# Change this to your secret key
app.secret_key = 'hospital_management_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '233301'  # Change this to your MySQL password
app.config['MYSQL_DB'] = 'mrk'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM users WHERE username = %s AND password = %s',
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            print("DEBUG ROLE:", user['role'])  # 👈 check karo console me

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            msg = 'Incorrect username/password!'

    return render_template('login.html', msg=msg)
# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        if user:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)', 
                         (username, email, password, role))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            
            if role == 'doctor':
                flash('Registration successful! Please login and complete your profile.', 'success')
            else:
                flash('Registration successful! Please login.', 'success')
            
            return redirect(url_for('login'))
    
    return render_template('register.html', msg=msg)

# Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# ==================== ADMIN PANEL ====================

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get counts
        cursor.execute('SELECT COUNT(*) as total FROM hospitals')
        total_hospitals = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM doctors')
        total_doctors = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM appointments')
        total_appointments = cursor.fetchone()['total']
        
        return render_template('admin/dashboard.html', 
                             total_hospitals=total_hospitals,
                             total_doctors=total_doctors,
                             total_users=total_users,
                             total_appointments=total_appointments)
    return redirect(url_for('login'))

# Add Hospital
@app.route('/admin/add_hospital', methods=['GET', 'POST'])
def add_hospital():
    if 'loggedin' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            address = request.form['address']
            city = request.form['city']
            phone = request.form['phone']
            email = request.form['email']
            
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO hospitals (name, address, city, phone, email) VALUES (%s, %s, %s, %s, %s)',
                         (name, address, city, phone, email))
            mysql.connection.commit()
            flash('Hospital added successfully!', 'success')
            return redirect(url_for('hospital_list'))
        
        return render_template('admin/add_hospital.html')
    return redirect(url_for('login'))

# Hospital List
@app.route('/admin/hospitals')
def hospital_list():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM hospitals')
        hospitals = cursor.fetchall()
        return render_template('admin/hospital_list.html', hospitals=hospitals)
    return redirect(url_for('login'))

# Delete Hospital
@app.route('/admin/delete_hospital/<int:id>')
def delete_hospital(id):
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM hospitals WHERE id = %s', (id,))
        mysql.connection.commit()
        flash('Hospital deleted successfully!', 'success')
        return redirect(url_for('hospital_list'))
    return redirect(url_for('login'))



# Doctor List
@app.route('/admin/doctors')
def doctor_list():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT d.*, h.name as hospital_name 
            FROM doctors d 
            JOIN hospitals h ON d.hospital_id = h.id
        ''')
        doctors = cursor.fetchall()
        return render_template('admin/doctor_list.html', doctors=doctors)
    return redirect(url_for('login'))

# Delete Doctor
@app.route('/admin/delete_doctor/<int:id>')
def delete_doctor(id):
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM doctors WHERE id = %s', (id,))
        mysql.connection.commit()
        flash('Doctor deleted successfully!', 'success')
        return redirect(url_for('doctor_list'))
    return redirect(url_for('login'))

# ==================== DOCTOR PANEL ====================

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'loggedin' in session and session['role'] == 'doctor':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get doctor info
        cursor.execute('''
            SELECT d.*, h.name as hospital_name 
            FROM doctors d 
            JOIN hospitals h ON d.hospital_id = h.id 
            WHERE d.user_id = %s
        ''', (session['id'],))
        doctor = cursor.fetchone()
        
        if not doctor:
            flash('Please complete your profile first!', 'warning')
            return redirect(url_for('doctor_profile'))
        
        # Get appointments
        cursor.execute('''
            SELECT a.*, u.username, u.email 
            FROM appointments a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.doctor_id = %s AND a.status = 'pending'
            ORDER BY a.appointment_date, a.appointment_time
        ''', (doctor['id'],))
        appointments = cursor.fetchall()
        
        return render_template('doctor/dashboard.html', doctor=doctor, appointments=appointments)
    return redirect(url_for('login'))

# Doctor Profile
@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    if 'loggedin' in session and session['role'] == 'doctor':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            name = request.form['name']
            hospital_id = request.form['hospital_id']
            specialization = request.form['specialization']
            qualification = request.form['qualification']
            experience = request.form['experience']
            phone = request.form['phone']
            email = request.form['email']
            fee = request.form['fee']
            available_days = request.form['available_days']
            available_time = request.form['available_time']
            
            # Check if profile exists
            cursor.execute('SELECT * FROM doctors WHERE user_id = %s', (session['id'],))
            doctor = cursor.fetchone()
            
            if doctor:
                cursor.execute('''
                    UPDATE doctors 
                    SET name=%s, hospital_id=%s, specialization=%s, qualification=%s,
                        experience=%s, phone=%s, email=%s, fee=%s, available_days=%s, available_time=%s
                    WHERE user_id=%s
                ''', (name, hospital_id, specialization, qualification, experience, 
                      phone, email, fee, available_days, available_time, session['id']))
            else:
                cursor.execute('''
                    INSERT INTO doctors (user_id, name, hospital_id, specialization, qualification,
                                        experience, phone, email, fee, available_days, available_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (session['id'], name, hospital_id, specialization, qualification, 
                      experience, phone, email, fee, available_days, available_time))
            
            mysql.connection.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('doctor_dashboard'))
        
        # Get doctor info for form
        cursor.execute('SELECT * FROM doctors WHERE user_id = %s', (session['id'],))
        doctor = cursor.fetchone()
        
        cursor.execute('SELECT * FROM hospitals')
        hospitals = cursor.fetchall()
        
        return render_template('doctor/profile.html', doctor=doctor, hospitals=hospitals)
    return redirect(url_for('login'))

# Doctor Appointments
@app.route('/doctor/appointments')
def doctor_appointments():
    if 'loggedin' in session and session['role'] == 'doctor':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get doctor
        cursor.execute('SELECT id FROM doctors WHERE user_id = %s', (session['id'],))
        doctor = cursor.fetchone()

        # 🔴 IMPORTANT CHECK
        if not doctor:
            flash("Please complete your profile first!", "warning")
            return redirect(url_for('doctor_profile'))

        # Fetch appointments
        cursor.execute('''
            SELECT a.*, u.username, u.email 
            FROM appointments a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (doctor['id'],))

        appointments = cursor.fetchall()

        return render_template('doctor/appointments.html', appointments=appointments)

    return redirect(url_for('login'))
# Add Prescription
@app.route('/doctor/prescription/<int:appointment_id>', methods=['GET', 'POST'])
def add_prescription(appointment_id):
    if 'loggedin' in session and session['role'] == 'doctor':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            diagnosis = request.form['diagnosis']
            medicines = request.form['medicines']
            instructions = request.form['instructions']
            followup_date = request.form['followup_date']
            
            cursor.execute('''
                INSERT INTO prescriptions (appointment_id, diagnosis, medicines, instructions, followup_date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (appointment_id, diagnosis, medicines, instructions, followup_date))
            
            cursor.execute('UPDATE appointments SET status = "completed" WHERE id = %s', (appointment_id,))
            mysql.connection.commit()
            
            flash('Prescription added successfully!', 'success')
            return redirect(url_for('doctor_appointments'))
        
        cursor.execute('''
            SELECT a.*, u.username, u.email 
            FROM appointments a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.id = %s
        ''', (appointment_id,))
        appointment = cursor.fetchone()
        
        return render_template('doctor/prescription.html', appointment=appointment)
    return redirect(url_for('login'))

# Update Appointment Status
@app.route('/doctor/update_appointment/<int:appointment_id>/<string:status>')
def update_appointment_status(appointment_id, status):
    if 'loggedin' in session and session['role'] == 'doctor':
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE appointments SET status = %s WHERE id = %s', (status, appointment_id))
        mysql.connection.commit()
        flash(f'Appointment {status}!', 'success')
        return redirect(url_for('doctor_appointments'))
    return redirect(url_for('login'))

# ==================== USER PANEL ====================

@app.route('/user/dashboard')
def user_dashboard():
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get upcoming appointments
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, h.name as hospital_name 
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.id 
            JOIN hospitals h ON a.hospital_id = h.id 
            WHERE a.user_id = %s AND a.appointment_date >= CURDATE()
            ORDER BY a.appointment_date, a.appointment_time
        ''', (session['id'],))
        appointments = cursor.fetchall()
        
        return render_template('user/dashboard.html', appointments=appointments)
    return redirect(url_for('login'))

# User Hospital List
@app.route('/user/hospitals')
def user_hospitals():
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM hospitals')
        hospitals = cursor.fetchall()
        return render_template('user/hospital_list.html', hospitals=hospitals)
    return redirect(url_for('login'))

# User Doctor List
@app.route('/user/doctors')
def user_doctors():
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT d.*, h.name as hospital_name 
            FROM doctors d 
            JOIN hospitals h ON d.hospital_id = h.id
        ''')
        doctors = cursor.fetchall()
        return render_template('user/doctor_list.html', doctors=doctors)
    return redirect(url_for('login'))

# User Doctor List by Hospital
@app.route('/user/doctors/<int:hospital_id>')
def user_doctors_by_hospital(hospital_id):
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT d.*, h.name as hospital_name 
            FROM doctors d 
            JOIN hospitals h ON d.hospital_id = h.id 
            WHERE d.hospital_id = %s
        ''', (hospital_id,))
        doctors = cursor.fetchall()
        
        cursor.execute('SELECT * FROM hospitals WHERE id = %s', (hospital_id,))
        hospital = cursor.fetchone()
        
        return render_template('user/doctor_list.html', doctors=doctors, hospital=hospital)
    return redirect(url_for('login'))

# Book Appointment
@app.route('/user/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    today = datetime.now().date()

    # 🔹 Login check
    if 'loggedin' not in session or session['role'] != 'user':
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 🔹 Doctor details fetch
    cursor.execute('''
        SELECT d.*, h.name as hospital_name 
        FROM doctors d 
        JOIN hospitals h ON d.hospital_id = h.id 
        WHERE d.id = %s
    ''', (doctor_id,))
    doctor = cursor.fetchone()

    if not doctor:
        return "Doctor not found"

    # 🔹 POST request (Form submit)
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        symptoms = request.form['symptoms']

        user_id = session.get('user_id')

        if not user_id:
            return "Please login first"

        cursor.execute('''
            INSERT INTO appointments 
            (user_id, doctor_id, hospital_id, appointment_date, appointment_time, symptoms)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, doctor_id, doctor['hospital_id'], appointment_date, appointment_time, symptoms))

        mysql.connection.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    # 🔹 GET request
    return render_template(
        'user/book_appointment.html',
        doctor=doctor,
        today=today
    )
# User Appointment History
@app.route('/user/history')
def user_history():
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, h.name as hospital_name,
                   p.diagnosis, p.medicines, p.instructions, p.followup_date
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.id 
            JOIN hospitals h ON a.hospital_id = h.id 
            LEFT JOIN prescriptions p ON a.id = p.appointment_id
            WHERE a.user_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (session['id'],))
        appointments = cursor.fetchall()
        
        return render_template('user/history.html', appointments=appointments)
    return redirect(url_for('login'))

# Cancel Appointment
@app.route('/user/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    if 'loggedin' in session and session['role'] == 'user':
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE appointments SET status = "cancelled" WHERE id = %s', (appointment_id,))
        mysql.connection.commit()
        flash('Appointment cancelled!', 'success')
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)