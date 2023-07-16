# Flask related modules
from flask import Blueprint, render_template, request, session, redirect, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_session import Session
from .models import booking, users, drivers, locations

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
    book_ids = []
    booked = []
    books = booking.query.all()
    for i in books:
        book_ids.append(i.book_id)
    from_users = users.query.all()
    for j in from_users:
        booked.append(j.book_id)
    for i in book_ids:	
        if i not in booked:
            book_del = booking.query.get(i)
            db.session.delete(book_del)
            db.session.commit()

def get_driver(user_id):
    d_id = users.query.filter_by(user_id=user_id).first()
    return d_id.driver_id

@app_views.route('/')
def home_page():
    """Displays the home page of our app"""
    return render_template('land.html')

@app_views.route('/admin')
def admin():
    """provides useful info to admin"""
    return render_template('admin.html')

@app_views.route('/reject', methods=['GET', 'POST'])
def reject_application():
    """rejects drivers' applications"""
    driver_id = request.form['driver_id']
    driver = drivers.query.filter_by(driver_id=driver_id).first()
    if driver:
        db.session.delete(driver)
        db.session.commit()
    return redirect('/validate_drivers')

@app_views.route('/validate_drivers')
def validation():
    new_drivers = drivers.query.filter_by(validated=False).all()
    return render_template('/validate.html', new_drivers=new_drivers)

@app_views.route('/drop-off', methods=['GET', 'POST'])
def drop():
    session.pop('book_id', None)
    all_users = users.query.filter_by(driver_id=session['driver_id']).all()
    for user in all_users:
        user.book_id = None
        user.driver_id = None
        db.session.commit()
    return redirect('/main-drivers')

@app_views.route('/cancel-booking', methods=['GET', 'POST'])
def cancel_request():
    """cancels user's booking"""
    booked = users.query.filter_by(user_id=session['user_id']).first()
    book_idd = booked.book_id
    booked = users.query.filter_by(user_id=session['user_id']).update({"book_id": None, "driver_id": None})
    book = booking.query.filter_by(book_id=book_idd).first()
    passengers = book.no_of_passengers
    book0 = booking.query.filter_by(book_id=book_idd).update({"no_of_passengers": passengers - 1})
    db.session.commit()
    return redirect('/main-riders')

@app_views.route('/validate', methods=['GET', 'POST'])
def validate():
    """"validates drivers"""
    driver_id = request.form['driver_id']
    driver = drivers.query.filter_by(driver_id=driver_id).update({"validated": 1})
    db.session.commit()
    return redirect('/validate_drivers')

@app_views.route('/add_locations', methods=['GET', 'POST'])
def add_location():
    """adds location to table"""
    if request.method == 'POST':
        location = request.form['location']
        city = request.form['city']
        loc = locations.query.filter_by(name=location, city=city).first()
        if loc:
            flash('Location already Exists')
            return render_template('addlocation.html')
        loc1 = locations(name=location, city=city)
        print('createdddddddddddddddddddddddd')
        db.session.add(loc1)
        db.session.commit()
        flash('New Location added')
        return render_template('addlocation.html')
    return render_template('addlocation.html')

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
        place = request.form['searched_name']
        booked = booking.query.filter_by(start=place.capitalize()).all()
        all_booked = []
        for i in booked:
            if i.no_of_passengers != 0:
                all_booked.append(i)
        return render_template('main-drivers.html', all_booked=all_booked)

@app_views.route('/main-drivers', methods=['GET', 'POST'])
def main_page_drivers():
    """Main page displayed for drivers"""
    if 'loggedin' in session:
        bk = []
        booked = users.query.all()
        for j in booked:
            if j.book_id != None:
                bk.append(j)
        all_booked = []
        for i in bk:
            b = booking.query.filter_by(book_id=i.book_id).first()
            if b.no_of_passengers != 0:
                all_booked.append(b)
        print(all_booked, '=======')
        return render_template('main-drivers.html', all_booked=all_booked)

@app_views.route('/main-riders', methods=['GET', 'POST'])
def main_page_riders():
    """Main page displayed for drivers"""
    if 'loggedin' in session: # to check if the rider is logged in
        all_loc = locations.query.all()
        if request.method == 'POST':
            pickup = request.form['pickup']
            destination = request.form['destination']
            print(pickup, destination, '-------------------------------')
            if pickup == destination:
                flash('Wrong input')
                return render_template('main-riders.html', all_loc=all_loc)
            # execute sql to add to the booking table
            sf = booking.query.all()
            print(sf)
            for i in sf:
                if i.start == pickup and i.finish == destination: # to check if there is the same booking
                    booking_1 = booking.query.filter_by(start=pickup, finish=destination).first()
                    booking_2 = users.query.filter_by(user_id=session['user_id']).first()
                    if booking_1.book_id == booking_2.book_id: # to check if the rider is booking again
                        d_id = get_driver(session['user_id'])  # -------------------------------------------------------------------------------------------
                        if d_id:
                            driver = drivers.query.filter_by(driver_id=d_id).first()
                            #we can tell the person they are already book by passing a string
                            flash('Already booked')
                            return render_template('driver-info.html', driver=driver, filename=driver.photo)
                        flash('Already Booked')
                        return render_template('driver-info.html')
                    # if user isnt already booked we will add the no_of_passengers and add book_id for user
                    passengers = booking.query.filter_by(start=pickup, finish=destination).first()
                    p = passengers.no_of_passengers + 1
                    print(p)
                    bb_0 = booking.query.filter_by(start=pickup, finish=destination).first()
                    bb_0.no_of_passengers = p
                    db.session.commit()
                    b = booking.query.filter_by(start=pickup, finish=destination).first()
                    print(b, '----------')
                    user1 = users.query.filter_by(user_id=session['user_id']).first()
                    db.session.commit()
                    # we clear booking that have no user associations
                    clear_bookings()
                    # return request sent
                    d_id = get_driver(session['user_id'])
                    if d_id:
                        driver = drivers.query.filter_by(driver_id=d_id).first()
                        return render_template('driver-info.html', driver=driver, filename=driver.photo)
                    return render_template('driver-info.html')
            # processes new booking requests
            id_book = users.query.filter_by(user_id=session['user_id']).first()
            print(id_book)
            if id_book.book_id != None: # deletes previous booking
                users0 = users.query.filter_by(user_id=session['user_id']).first()
                users0.book_id = None
                db.session.commit()
                passenger_no = booking.query.filter_by(book_id=id_book.book_id)
                users1 = booking.query.filter_by(book_id=id_book.book_id).first()
                users1.no_of_passengers = users1.no_of_passengers - 1
                db.session.commit()
            user_new = booking(start=pickup, finish=destination, no_of_passengers=1)
            db.session.add(user_new)
            db.session.commit()
            b = booking.query.filter_by(start=pickup, finish=destination).first()
            users2 = users.query.filter_by(user_id=session['user_id']).first()
            users2.book_id = b.book_id
            users2.driver_id = None
            db.session.commit()
            clear_bookings()
            d_id = get_driver(session['user_id'])
            if d_id:
                cur.execute('select * from drivers where driver_id=%s', (d_id,))
                driver = drivers.query.filter_by(driver_id=d_id).all()
                return render_template('driver-info.html', driver=driver, filename=driver.photo)
            return render_template('driver-info.html')
        return render_template('main-riders.html', all_loc=all_loc)
    return 'you must login to access this page'

@app_views.route('/take-offer', methods=['GET', 'POST'])
def take_offers():
    """Responds to the riders' request"""
    if 'loggedin' in session:
        if request.method == 'POST':
            book_idd = request.form['book_request']
            b = booking.query.filter_by(book_id=session['book_id']).first()
            if 'book_id' in session and b.no_of_passengers >= 0:
                if book_idd != session['book_id']:
                    rider_list = users.query.filter_by(driver_id=session['driver_id']).all()
                    book3 = booking.query.filter_by(book_id=session['book_id']).first()
                    flash('You took an offer already')
                    return render_template('rider-list.html', rider_list=rider_list, book3=book3)
            #print(book_idd)
            session['book_id'] = book_idd
            book0 = booking.query.filter_by(book_id=book_idd).first()
            # we have no of booked people on a certain booking
            no_of_booked_passengers = book0.no_of_passengers
            # we have the list of users who have been assigned to this driver
            rider_list = users.query.filter_by(driver_id=session['driver_id']).all()
            driver0 = drivers.query.filter_by(driver_id=session['driver_id']).first()
            no_of_seats = driver0.seats
            if len(rider_list) == no_of_seats:
                flash('It is full')
                return render_template('rider-list.html', rider_list=rider_list)
            users1 = users.query.filter_by(book_id=book_idd, driver_id=None).all()
            for i in users1:
                updated_booked_no = users.query.filter_by(driver_id=session['driver_id']).all()
                if len(updated_booked_no) == no_of_seats:
                    break
                book1 = booking.query.filter_by(book_id=book_idd).first()
                user2 = users.query.filter_by(user_id=i.user_id).update({"driver_id": session['driver_id']})
                book2 = booking.query.filter_by(book_id=book_idd).update({"no_of_passengers": int(book1.no_of_passengers - 1)})
                db.session.commit()
            rider_list = users.query.filter_by(driver_id=session['driver_id']).all()
            book3 = booking.query.filter_by(book_id=session['book_id']).first()
            return render_template('rider-list.html', rider_list=rider_list, book3=book3)
    return 'Login to access this page'
