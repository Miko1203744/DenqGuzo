from . import db

class users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    created_on = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('booking.book_id'), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'), nullable=True)

    def __repr__(self):
        return '{} {} {}'.format(self.email, self.password, self.username)

class booking(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.String(50))
    finish = db.Column(db.String(50))
    no_of_passengers = db.Column(db.Integer, default=0)
    user = db.relationship('users', backref='booking')

    def __repr__(self):
        return "<Item>: {} ... {}".format(self.start, self.finish)

class drivers(db.Model):
    driver_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    city = db.Column(db.String(100))
    photo = db.Column(db.String(100))
    license = db.Column(db.String(100))
    plate_number = db.Column(db.String(100), unique=True)
    created_on = db.Column(db.DateTime)
    seats = db.Column(db.Integer)
    validated = db.Column(db.Boolean, default=False, index=True)
    user = db.relationship('users', backref='drivers')

    def __repr__(self):
        return "user: {} item: {}".format(self.username, self.driver_id)


class locations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(100))

    def __repr__(self):
        return "<order>: {} ... {}".format(self.name, self.city)