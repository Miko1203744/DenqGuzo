from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_session import Session
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
        cur = db.connection.cursor()
        #do some fetching to check if email already exists
        cur.execute('SELECT email FROM users where email=%s', (email,))
        data = cur.fetchone()
        #print(data)
        if data:
            flash('Email already exists')
            return render_template('signup.html')
        cur.execute('SELECT username FROM users where username=%s', (username,))
        if cur.fetchone():
            flash('Username already exists')
            return render_template('signup.html')
        db.connection.commit()
        cur.close()
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
        cur = db.connection.cursor()
        cur.execute('SELECT EMAIL FROM USERS WHERE EMAIL=%s', (email, ))
        user = cur.fetchone()
        if user:
            cur.execute('SELECT PASSWORD FROM USERS WHERE EMAIL=%s', (email,))
            p = cur.fetchone()
            if p:
                if check_password_hash(p[0], pwd):
                    cur.execute('SELECT user_id FROM USERS WHERE EMAIL=%s and PASSWORD=%s', (email, p[0],))
                    data = cur.fetchone()
                    print(data)
                    session['user_id'] = data[0]
                    session['email'] = email
                    session['pwd'] = pwd
                    session['loggedin'] = True
                    cur.execute('SELECT USERNAME FROM USERS WHERE EMAIL=%s and PASSWORD=%s', (email, p[0],))
                    un = cur.fetchone()
                    print(un)
                    session['username'] = un[0]
                    #cur.execute('SELECT USERNAME FROM USERS WHERE EMAIL=%s and PASSWORD=%s and IS_ADMIN=%s', (email, p[0], True, ))
                    #a = cur.fetchone()
                    #if a:
                    #    session['is_admin'] = True 
                    db.connection.commit()
                    cur.close()
                    return redirect('/main-riders')
                flash('Incorrect password')
                return render_template('rlogin.html')
        if user is None:
            flash('Invalid email or password')
    return render_template("rlogin.html")

@app_auth_riders.route('/logout-riders', methods=['GET'])
def logout():
    # also delete their bookings
    cur = db.connection.cursor()
    cur.execute('update users set book_id=NULL where user_id=%s', (session['user_id'],))
    cur.execute('update users set driver_id=NULL where user_id=%s', (session['user_id'],))
    db.connection.commit()
    cur.close()
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
            cur = db.connection.cursor()
            #do some fetching to check if email already exists
            cur.execute('INSERT INTO users (username, email, password, created_on) values(%s, %s, %s, %s)', (username, email, generate_password_hash(pwd), datetime.now(),))
            db.connection.commit()
            cur.close()
            session.pop('email', None)
            session.pop('pwd', None)
            session.pop('username', None)
            return redirect('/login-riders')
        else:
            flash('Incorrect Input')
    return render_template('otp.html')
