from . import db
from flask_login import UserMixin


class User(UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    is_admin = db.Column(db.Boolean, default=False, index=True)

    def __repr__(self):
        return '{} {} {}'.format(self.email, self.password, self.username)


