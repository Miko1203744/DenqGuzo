# Flask related modules
from flask import Blueprint, render_template, request, session, redirect, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_session import Session

from datetime import datetime
from os import environ
import requests, json
from geopy.geocoders import Nominatim
from geopy import distance
from geopy.distance import geodesic

app_views = Blueprint('app_views', __name__)

def get_location_by_ip(ip_addr):
    url = "https://ipgeolocation.abstractapi.com/v1/?api_key={}&ip_address={}".format(environ.get('API_KEY_ABSTRACT'), ip_addr)
    response = requests.get(url)
    a = json.loads(response.content.decode('utf-8'))
    lon = a['longitude']
    lat = a['latitude']
    return (lon, lat)

def get_distance(ip_addr, name):
    url = "https://geocode.search.hereapi.com/v1/geocode?q={}, Addis Ababa&limit=4&apiKey={}".format(name, environ.get('API_KEY_HERE'))
    response = requests.get(url)
    a = json.loads(response.content.decode('utf-8'))
    lon = a['items'][0]['position']['lng']
    lat = a['items'][0]['position']['lat']
    loc1 = (lon, lat)
    loc2 = get_location_by_ip(ip_addr)
    h = geodesic(loc1, loc2).km
    return h

def clear_bookings():
    cur = db.connection.cursor()
    cur.execute('select book_id from booking')
    books = cur.fetchall()
    cur.execute('select book_id from users')
    from_users = cur.fetchall()
    for i in books:
        if i not in from_users:
            cur.execute('delete from booking where book_id=%s', (i[0],))
    db.connection.commit()
    cur.close()

def get_driver(user_id):
    cur = db.connection.cursor()
    cur.execute('SELECT DRIVER_ID from users where user_id=%s', (user_id,))
    d_id = cur.fetchone()
    return d_id[0]

@app_views.route('/')
def home_page():
    """Displays the home page of our app"""
    return render_template('land.html')

@app_views.route('/about')
def about_page():
    """Displays the about page of our app"""
    return render_template('about.html')

@app_views.route('/profile')
def profile():
    """Displays personal information of the user
    """
    if 'loggedin' in session:
        # we can add more info about the user
        return render_template('profile.html', name=session['username'], email=session['email'])
    return redirect('/login')

@app_views.route('/search', methods=['GET', 'POST'])
def search():
    """allows drivers to search for booked places"""
    if 'loggedin' in session:
        cur = db.connection.cursor()
        place = request.form['searched_name']
        cur.execute('SELECT book_id from users where book_id <> "null"')
        booked = cur.fetchall()
        all_booked = []
        for i in booked:
            cur.execute('SELECT START, FINISH, NO_OF_PASSENGERS, BOOK_ID FROM BOOKING WHERE BOOK_ID=%s and start=%s', (i[0], place,))
            b = cur.fetchone()
            if b:
                if b[2] != 0:
                    all_booked.append(b)
        print(all_booked, '++++++++++++++++++++++++++')
        db.connection.commit()
        cur.close()
        return render_template('main-drivers.html', all_booked=all_booked)

@app_views.route('/main-drivers', methods=['GET', 'POST'])
def main_page_drivers():
    """Main page displayed for drivers"""
    if 'loggedin' in session:
        cur = db.connection.cursor()
        cur.execute('SELECT book_id from users where book_id <> "null"')
        booked = cur.fetchall()
        all_booked = []
        for i in booked:
            cur.execute('SELECT START, FINISH, NO_OF_PASSENGERS, BOOK_ID FROM BOOKING WHERE BOOK_ID=%s', (i[0],))
            b = cur.fetchone()
            if b[2] != 0:
                all_booked.append(b)
        print(all_booked, '=======')
        db.connection.commit()
        cur.close()
        return render_template('main-drivers.html', all_booked=all_booked)

@app_views.route('/main-riders', methods=['GET', 'POST'])
def main_page_riders():
    """Main page displayed for drivers"""
    if 'loggedin' in session: # to check if the rider is logged in
        cur = db.connection.cursor()
        cur.execute('SELECT * from locations')
        all_loc = cur.fetchall()
        db.connection.commit()
        cur.close()
        if request.method == 'POST':
            pickup = request.form.get('pickup')
            destination = request.form.get('destination')
            print(pickup, destination, '--------------')
            if pickup == destination:
                flash('Wrong input')
                return render_template('main-riders.html', all_loc=all_loc)
            # execute sql to add to the booking table
            cur = db.connection.cursor()
            cur.execute('SELECT START, FINISH FROM BOOKING')
            sf = cur.fetchall()
            print(sf)
            for i in sf:
                if i[0] == pickup and i[1] == destination: # to check if there is the same booking
                    cur.execute('select book_id from booking where start=%s and finish=%s', (pickup, destination, ))
                    booking_1 = cur.fetchone()
                    cur.execute('select book_id from users where user_id=%s', (session['user_id'],))
                    booking_2 = cur.fetchone()
                    if booking_1 == booking_2: # to check if the rider is booking again
                        d_id = get_driver(session['user_id'])
                        if d_id:
                            cur.execute('select * from drivers where driver_id=%s', (d_id,))
                            driver = cur.fetchone()
                            db.connection.commit()
                            cur.close()
                            #we can tell the person they are lready book by passing a string
                            #flash('Already booked')
                            return render_template('driver-info.html', driver=driver, filename=driver[6])
                        #flash('Already Booked')
                        return render_template('driver-info.html')
                        #return 'Already Booked'
                    # if user isnt already booked we will add the no_of_passengers and add book_id for user
                    cur.execute('select no_of_passengers from booking where start=%s and finish=%s', (pickup, destination, ))
                    passengers = cur.fetchone()
                    p = passengers[0] + 1
                    print(p)
                    cur.execute('UPDATE BOOKING set no_of_passengers=%s where start=%s and finish=%s', (p, pickup, destination, ))
                    cur.execute('select book_id from booking where start=%s and finish=%s', (pickup, destination,))
                    b = cur.fetchone()
                    print(b, '----------')
                    cur.execute('UPDATE users set book_id=%s where user_id=%s', (b[0], session['user_id'], ))
                    #cur.execute('UPDATE users set driver_id=NULL where user_id=%s', (session['user_id'],))
                    # we clear booking that have no user associations
                    clear_bookings()
                    # return request sent
                    d_id = get_driver(session['user_id'])
                    if d_id:
                        cur.execute('select * from drivers where driver_id=%s', (d_id,))
                        driver = cur.fetchone()
                        db.connection.commit()
                        cur.close()
                        return render_template('driver-info.html', driver=driver, filename=driver[6])
                    db.connection.commit()
                    cur.close()
                    return render_template('driver-info.html')
            # processes new booking requests
            cur = db.connection.cursor()
            cur.execute('SELECT BOOK_ID FROM USERS WHERE USER_ID=%s', (session['user_id'],))
            id_book = cur.fetchone()
            print(id_book)
            if id_book[0] != None: # deletes previous booking
                cur.execute('update users set book_id=NULL where user_id=%s', (session['user_id'],))
                cur.execute('select no_of_passengers from booking where book_id=%s', (id_book,))
                passenger_no = cur.fetchone()
                cur.execute('update booking set no_of_passengers=%s where book_id=%s', (passenger_no[0] - 1, id_book,))
            cur.execute('INSERT INTO BOOKING (start, finish, no_of_passengers) values(%s, %s, %s)', ( pickup, destination, 1))
            cur.execute('select book_id from booking where start=%s and finish=%s', (pickup, destination,))
            b = cur.fetchone()
            cur.execute('UPDATE users set book_id=%s where user_id=%s', (b[0], session['user_id'], ))
            cur.execute('UPDATE users set driver_id=NULL where user_id=%s', (session['user_id'],))
            clear_bookings()
            d_id = get_driver(session['user_id'])
            if d_id:
                cur.execute('select * from drivers where driver_id=%s', (d_id,))
                driver = cur.fetchone()
                db.connection.commit()
                cur.close()
                return render_template('driver-info.html', driver=driver)
            db.connection.commit()
            cur.close()
            return render_template('driver-info.html')
        return render_template('main-riders.html', all_loc=all_loc)
    return 'you must login to access this page'

@app_views.route('/take-offer', methods=['GET', 'POST'])
def take_offers():
    """Responds to the riders' request"""
    if 'loggedin' in session:
        book_idd = request.form['book_request']
        cur = db.connection.cursor()
        cur.execute('SELECT NO_OF_PASSENGERS FROM BOOKING WHERE BOOK_ID=%s', (book_idd,))
        no_of_booked = cur.fetchone()
        cur.execute('SELECT USER_ID FROM USERS WHERE DRIVER_ID=%s', (session['driver_id'],))
        no_of_pass = cur.fetchall()
        cur.execute('SELECT SEATS FROM DRIVERS WHERE DRIVER_ID=%s', (session['driver_id'],))
        no_of_seats = cur.fetchall()
        if no_of_pass == no_of_seats:
            cur.execute('select username, user_id from users where driver_id=%s', (session['driver_id'],))
            rider_list = cur.fetchall()
            flash('It is full')
            return render_template('rider-list.html', rider_list=rider_list)
        cur.execute('SELECT user_id from USERS WHERE BOOK_ID=%s AND DRIVER_ID IS NULL', (book_idd,))
        users1 = cur.fetchall()
        for i in users1:
            print(i)
            cur.execute('SELECT USER_ID FROM USERS WHERE DRIVER_ID=%s', (session['driver_id'],))
            no_of_passengerz = cur.fetchall()
            if len(no_of_passengerz) == no_of_seats:
                break
            cur.execute('update users set driver_id=%s where user_id=%s', (session['driver_id'], i,))
            cur.execute('update booking set no_of_passengers=%s where book_id=%s', (no_of_booked[0] - 1 ,book_idd,))
        cur.execute('select username, user_id from users where driver_id=%s', (session['driver_id'],))
        rider_list = cur.fetchall()
        print(rider_list)
        db.connection.commit()
        cur.close()
        return render_template('rider-list.html', rider_list=rider_list)
        return 
    return 'Login to access this page'
