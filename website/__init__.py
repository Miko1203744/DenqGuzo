from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
#install sqlalchemy
from flask_mail import Mail, Message
from flask_session import Session

from geopy.geocoders import Nominatim
from geopy import distance
import requests, json
from os import environ

app = Flask(__name__)

#db = MySQL(app)
db = SQLAlchemy()
app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///denqguzo.db'
db.init_app(app)
mail = Mail(app)
Session(app)

from .auth_riders import app_auth_riders
from .auth_drivers import app_auth_drivers
from .views import app_views

app.register_blueprint(app_auth_riders, url_prefix='/')
app.register_blueprint(app_auth_drivers, url_prefix='/')
app.register_blueprint(app_views, url_prefix='/')

#API_KEY = environ.get('API_KEY')
#geolocator = Nominatim(user_agent="app")
#location = geolocator.geocode("Gofa sefer, Addis Ababa")
# print raw data
#print(location.raw)


from .models import users, locations, booking, drivers
with app.app_context():
    db.create_all()



