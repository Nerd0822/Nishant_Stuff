from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from flask_mysqldb import MySQL
import bcrypt
import re
import logging
import sys

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# MySQL database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'nomos_legal'
mysql = MySQL(app)

# Logging configuration
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Utility: Validate email format
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Utility: Hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Utility: Check hashed password
def check_password(hashed, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Route: Home
@app.route('/')
def home():
    return render_template('index.html')

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Please fill out the form!'}), 400

        cursor = mysql.connection.cursor()
        try:
            # Fetch user by email
            cursor.execute('SELECT * FROM user_account WHERE user_email = %s', (email,))
            account = cursor.fetchone()

            if account and check_password(account[3].encode('utf-8'), password):
                session['loggedin'] = True
                session['user_id'] = account[0]
                session['username'] = account[1]
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                return jsonify({'success': False, 'message': 'Incorrect email or password!'}), 401
        except Exception as e:
            logging.error(f"Error during login: {e}")
            return jsonify({'success': False, 'message': 'An error occurred during login.'}), 500
        finally:
            cursor.close()

    return render_template('login.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('home'))

# Route: Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not username or not password or not email:
            return render_template('signup.html', msg='Please fill out the form!')

        if not is_valid_email(email):
            return render_template('signup.html', msg='Invalid email address!')

        if not re.match(r'[A-Za-z0-9]+', username):
            return render_template('signup.html', msg='Username must contain only letters and numbers!')

        cursor = mysql.connection.cursor()
        try:
            # Check for existing account
            cursor.execute('SELECT * FROM user_account WHERE user_email = %s', (email,))
            if cursor.fetchone():
                return render_template('signup.html', msg='Account already exists!')

            # Insert new user
            hashed_password = hash_password(password)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'INSERT INTO user_account (user_name, user_email, user_password, time_stamp) VALUES (%s, %s, %s, %s)',
                (username, email, hashed_password.decode('utf-8'), timestamp)
            )
            mysql.connection.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error during signup: {e}")
            return render_template('signup.html', msg='An error occurred during registration.')
        finally:
            cursor.close()

    return render_template('signup.html')

# Static routes
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/why')
def why():
    return render_template('why.html')

@app.route('/services')
def services():
    return render_template('service.html')

if __name__ == '__main__':
    app.run(debug=True)
