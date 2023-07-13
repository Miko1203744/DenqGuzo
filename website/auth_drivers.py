from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_session import Session

from . import db, mail
import random, math, os
from datetime import datetime
from os import environ

app_auth_drivers = Blueprint('app_auth_drivers', __name__)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
  
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app_auth_drivers.route('/sign-up-drivers', methods=['GET', 'POST'])
def signup():
    """sign up page for user"""
    digits = "0123456789"
    OTP = ""
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form and 'email' in request.form and 'plate' in request.form and 'seats' in request.form and 'license' in request.files and 'photo' in request.files:
            license = request.files['license']
            photo = request.files['photo']
            if license.filename == '':
                flash('Please upload a photo of your License')
                return render_template('dsignup.html')
            if photo.filename == '':
                flash('Please upload your photo')
                return render_template('dsignup.html')
            if not allowed_file(license.filename) or not allowed_file(photo.filename):
                flash('Please upload images only')
                return render_template('dsignup.html')
            email = request.form['email'].lower()
            pwd = request.form['password']
            username = request.form['username'].capitalize()
            plate = request.form['plate']
            seats = request.form['seats']
            session['email'] = email
            session['pwd'] = pwd
            session['username'] = username
            session['plate'] = plate
            session['seats'] = seats
            session['license'] = license.filename
            session['photo'] = photo.filename
            license.save(os.path.join(environ.get("UPLOAD_FOLDER"), license.filename))
            photo.save(os.path.join(environ.get("UPLOAD_FOLDER"), photo.filename))
            cur = db.connection.cursor()
            #do some fetching to check if email already exists
            cur.execute('SELECT email FROM drivers where email=%s', (email,))
            data = cur.fetchone()
            #print(data)
            if data:
                flash('Email already exists')
                return render_template('dsignup.html')
            cur.execute('SELECT username FROM drivers where username=%s', (username,))
            if cur.fetchone():
                flash('Username already exists')
                return render_template('dsignup.html')
            cur.execute('SELECT plate_number FROM drivers where plate_number=%s', (plate,))
            if cur.fetchone():
                flash('plate number already exists')
                return render_template('dsignup.html')
            #cur.execute('INSERT INTO DRIVERS (username, plate_number, email, password, photo, license, seats) values (%s, %s, %s, %s, %s, %s, %s, %s)', (username, plate, email, password, photo.filename, license.filename, seats, ))
            db.connection.commit()
            cur.close()
            for i in range(4):
                OTP += digits[math.floor(random.random() * 10)]
            msg = Message("DenqGuzo", sender = 'socbeza13@gmail.com', recipients = [email])
            msg.body = 'Your verification code is: ' + OTP + '. \nEnter this code on the signup page to proceed!'
            mail.send(msg)
            session['otp'] = OTP
            #save the otp code is session
            return redirect('/otp-drivers')
        elif 'license' not in request.files or 'photo' not in request.files:
            flash('Please upload both files')
            return render_template('dsignup.html')
        else:
            flash('Please fill out every input')
            return render_template('dsignup.html')
    return render_template('dsignup.html')

@app_auth_drivers.route('/login-drivers', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'password' in request.form and 'email' in request.form:
        email = request.form['email'].lower()
        pwd = request.form['password']
        cur = db.connection.cursor()
        cur.execute('SELECT EMAIL FROM DRIVERS WHERE EMAIL=%s', (email, ))
        user = cur.fetchone()
        if user:
            cur.execute('SELECT PASSWORD FROM DRIVERS WHERE EMAIL=%s', (email,))
            p = cur.fetchone()
            if p:
                if check_password_hash(p[0], pwd):
                    cur.execute('SELECT driver_id FROM DRIVERS WHERE EMAIL=%s and PASSWORD=%s', (email, p[0],))
                    data = cur.fetchone()
                    print(data)
                    session['driver_id'] = data[0]
                    session['email'] = email
                    session['pwd'] = pwd
                    session['loggedin'] = True
                    cur.execute('SELECT USERNAME FROM DRIVERS WHERE EMAIL=%s and PASSWORD=%s', (email, p[0],))
                    un = cur.fetchone()
                    print(un)
                    session['username'] = un[0]
                    cur.execute('SELECT * FROM DRIVERS WHERE EMAIL=%s and PASSWORD=%s and VALIDATED=True', (email, p[0], ))
                    valid = cur.fetchone()
                    db.connection.commit()
                    cur.close()
                    if valid:
                        return redirect('/main-drivers')
                    else:
                        return 'your application is being reviewed'
                    # redirect successsfully logged n users to a drivers main page
                flash('Incorrect password!')
                return render_template('dlogin.html')
        if user is None:
            flash('Invalid username or email')
    return render_template("dlogin.html")

@app_auth_drivers.route('/logout-drivers', methods=['GET'])
def logout():
    session.pop('driver_id', None)
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('username', None)
    session.pop('pwd', None)
    return redirect('/')

@app_auth_drivers.route('/otp-drivers', methods=['GET', 'POST'])
def otp_check_drivers():
    """checks if the sent otp and the user input are the same"""
    if request.method == 'POST':
        otp = session.get('otp')
        if otp == request.form['code']:
            session.pop('otp', None)
            email = session['email']
            pwd = generate_password_hash(session['pwd'])
            username = session['username']
            plate = session['plate']
            photo = session['photo']
            license = session['license']
            seats = session['seats']
            cur = db.connection.cursor()
            #do some fetching to check if email already exists
            cur.execute('INSERT INTO DRIVERS (username, plate_number, email, password, photo, license, seats, city) values (%s, %s, %s, %s, %s, %s, %s, %s)', (username, plate, email, pwd, photo, license, seats, 'Addis Ababa', ))
            #cur.execute('INSERT INTO users (username, email, password, created_on) values(%s, %s, %s, %s)', (username, email, generate_password_hash(pwd), datetime.now(),))
            db.connection.commit()
            cur.close()
            session.pop('email', None)
            session.pop('pwd', None)
            session.pop('username', None)
            session.pop('plate', None)
            session.pop('license', None)
            session.pop('seats', None)
            session.pop('photo', None)
            return redirect('/login-drivers')
        else:
            flash('Incorrect Input')
    return render_template('otp-drivers.html')
