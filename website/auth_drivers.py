from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from .models import booking, drivers
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
            #do some fetching to check if email already exists
            data = drivers.query.filter_by(email=email).first()
            if data:
                flash('Email already exists')
                return render_template('dsignup.html')
            un = drivers.query.filter_by(username=username).first()
            if un:
                flash('Username already exists')
                return render_template('dsignup.html')
            pn = drivers.query.filter_by(plate_number=plate).first()
            if pn:
                flash('plate number already exists')
                return render_template('dsignup.html')
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
        driver = drivers.query.filter_by(email=email).first()
        if driver is not None and check_password_hash(driver.password, pwd):
            session['driver_id'] = driver.driver_id
            session['email'] = email
            session['pwd'] = pwd
            session['loggedin'] = True
            session['username'] = driver.username
            if driver.validated == 1:
                return redirect('/main-drivers')
            else:
                return 'your application is being reviewed'
        if driver is None:
            flash('Invalid username or email')
        elif check_password_hash(driver.password, pwd) == False:
            flash('Incorrect password!')
    return render_template("dlogin.html")

@app_auth_drivers.route('/logout-drivers', methods=['GET'])
def logout():
    session.pop('driver_id', None)
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('username', None)
    session.pop('pwd', None)
    session.pop('book_id', None)
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
            #do some fetching to check if email already exists
            driver = drivers(username=username , plate_number=plate , email=email , password=pwd , photo=photo , license=license , seats=seats , city='Addis Ababa', created_on=datetime.now())
            db.session.add(driver)
            db.session.commit()
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
