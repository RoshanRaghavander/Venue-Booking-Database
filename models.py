#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    description = db.Column(db.String(500), default='')
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(500), default='')
    website = db.Column(db.String(120), nullable=True)
    genres = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Venue id: {self.id}, \
        name: {self.name}, \
        city: {self.city}, \
        state: {self.state}, \
        image_link: {self.image_link}, \
        address: {self.address}, \
        phone: {self.phone}, \
        facebook_link: {self.facebook_link}, \
        description: {self.description}, \
        seeking_talent: {self.seeking_talent}, \
        seeking_description: {self.seeking_description}, \
        website: {self.website}, \
        genres: {self.genres}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120), default=None, nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    shows = db.relationship('Show', backref="artist", lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Artist id: {self.id}, \
        name: {self.name}, \
        city: {self.city}, \
        state: {self.state}, \
        phone: {self.phone}, \
        image_link: {self.image_link}, \
        genres: {self.genres}, \
        facebook_link: {self.facebook_link}, \
        website: {self.website}, \
        seeking_venue: {self.seeking_venue}, \
        seeking_description: {self.seeking_description}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__= 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self) -> str:
        return f'<Show id: {self.id}, \
        artist_id: {self.artist_id}, \
        venue_id: {self.venue_id}, \
        start_time: {self.start_time}>'
