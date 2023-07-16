from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_session import Session
from .models import users

from . import db, mail
import random, math
from datetime import datetime

app_auth_riders = Blueprint('app_auth', __name__)

@app_auth_riders.route('/sign-up-riders', methods=['GET', 'POST'])
def signup():
    """sign up page for user"""
    digits = "0123456789"
    OTP = ""
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        email = request.form['email'].lower()
        pwd = request.form['password']
        username = request.form['username'].capitalize()
        session['email'] = email
        session['pwd'] = pwd
        session['username'] = username
        data = users.query.filter_by(email=email).first()
        if data:
            flash('Email already exists')
            return render_template('rsignup.html')
        #cur.execute('SELECT username FROM users where username=%s', (username,))
        un = users.query.filter_by(username=username).first()
        if un:
            flash('Username already exists')
            return render_template('rsignup.html')
        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]
        msg = Message("Denqguzo", sender = 'socbeza13@gmail.com', recipients = [request.form['email']])
        msg.body = 'Your verification code is: ' + OTP + '. \nEnter this code on the signup page to proceed!'
        mail.send(msg)
        session['otp'] = OTP
        #save the otp code is session
        return redirect('/otp-riders')
    return render_template('rsignup.html')

@app_auth_riders.route('/login-riders', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'password' in request.form and 'email' in request.form:
        email = request.form['email'].lower()
        pwd = request.form['password']
        user = users.query.filter_by(email=email).first()
        print(user)
        if user is not None and check_password_hash(user.password, pwd):
            #cur.execute('SELECT PASSWORD FROM USERS WHERE EMAIL=%s', (email,))
            session['user_id'] = user.user_id
            session['email'] = email
            session['pwd'] = pwd
            session['loggedin'] = True
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect('/main-riders')
        if user is None:
            flash('Invalid username or email')
        elif check_password_hash(user.password, pwd) == False:
            flash('Incorrect password!')
    return render_template("rlogin.html")

@app_auth_riders.route('/logout-riders', methods=['GET'])
def logout():
    user = users.query.filter_by(user_id=session['user_id']).first()
    user.book_id = None
    user.driver_id = None
    db.session.add(user)
    db.session.commit()
    session.pop('user_id', None)
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('username', None)
    session.pop('pwd', None)
    session.pop('is_admin', None)
    return redirect('/')

@app_auth_riders.route('/otp-riders', methods=['GET', 'POST'])
def otp_check():
    """checks if the sent otp and the user input are the same"""
    if request.method == 'POST':
        otp = session.get('otp')
        print(otp, '=======================')
        if otp == request.form['code']:
            session.pop('otp', None)
            email = session['email']
            pwd = session['pwd']
            username = session['username']
            #cur = db.connection.cursor()
            #do some fetching to check if email already exists
            #cur.execute('INSERT INTO users (username, email, password, created_on) values(%s, %s, %s, %s)', (username, email, generate_password_hash(pwd), datetime.now(),))
            user1 = users(username=username, email=email, password=generate_password_hash(pwd), created_on=datetime.now())
            db.session.add(user1)
            db.session.commit()
            session.pop('email', None)
            session.pop('pwd', None)
            session.pop('username', None)
            return redirect('/login-riders')
        else:
            flash('Incorrect Input')
    return render_template('otp.html')
