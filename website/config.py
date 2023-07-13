from os import environ, path
from dotenv import load_dotenv

# Specificy a `.env` file containing key/value config values
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))

FLASK_RUN_PORT = environ.get("FLASK_RUN_PORT")
ENVIRONMENT = environ.get("FLASK_ENV")
FLASK_APP = environ.get("FLASK_APP")
FLASK_DEBUG = environ.get("FLASK_DEBUG")

MYSQL_HOST = environ.get("MYSQL_HOST")
MYSQL_USER = environ.get("MYSQL_USER")
MYSQL_DB = environ.get("MYSQL_DB")
MYSQL_PASSWORD = environ.get("MYSQL_PASSWORD")

MAIL_SERVER = environ.get("MAIL_SERVER")
MAIL_PORT = environ.get("MAIL_PORT")
MAIL_USERNAME = environ.get("MAIL_USERNAME")
MAIL_PASSWORD= environ.get("MAIL_PASSWORD")
#MAIL_USE_TLS = environ.get("MAIL_USE_TLS") # dont use this
MAIL_USE_SSL = environ.get("MAIL_USE_SSL")
SESSION_PERMANENT = environ.get("SESSION_PERMANENT")
SESSION_TYPE = environ.get("SESSION_TYPE")
SECRET_KEY = environ.get("SECRET_KEY")
