# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
import dateutil.parser
import babel
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import load_only
from sqlalchemy import func, and_
from sqlalchemy.inspection import inspect
from models import*
#----------------------------------------------------------------------------#
# app Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

# load configurations from config.py
app.config.from_object('config')

# Alternatively, set configurations manually:
'''
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/roshan'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
'''
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

    # a query on Venues table aggregated by city and state names (areas)
    distinct_areas = Venue.query.options(load_only('city', 'state')).with_entities(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
    # options(load_only(
    data = list()
    current_time = datetime.now()

    #loop over all areas to check for upcoming shows
    for area in distinct_areas:
        area_data = dict()
        area_data['city'], area_data['state'] = area
        venues = Venue.query.filter_by(city=area_data['city']).filter_by(state=area_data['state']).all()
        area_data['venues'] = [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": db.session.query(Show).filter(Show.venue_id==venue.id, Show.start_time>current_time).all()[0][0]
                  } for venue in venues]
        data.append(area_data)

    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    # parse search term and use it for filter the query
    search_term = request.form.get('search_term', '')
    venue_search_result = db.session.query(Venue).options(load_only('id', 'name')).filter(Venue.name.like(f'%{search_term}%')).all()
    response = dict()
    response['count'] = len(venue_search_result)
    data = list()
    current_time = datetime.now()

    # loop over all search results from returned query and append it to list
    for venue in venue_search_result:
        venue_response = dict()
        venue_response['id'], venue_response['name'] = venue.id, venue.name
        upcoming_shows = db.session.query(Show).filter(and_(Show.venue_id == venue.id, Show.start_time > current_time)).all()
        venue_response['num_upcoming_shows'] = len(upcoming_shows)
        data.append(venue_response)

    # parse response dictionary
    response['data'] = data

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

    # query venues table by input venue_id
    venue_table_attributes = inspect(Venue).c
    attribute_list = [attribute.name for attribute in venue_table_attributes]
    venue = db.session.query(Venue).with_entities(*attribute_list).filter(Venue.id == venue_id).all()
    current_time = datetime.now()

    # find past and upcoming shows using input venue_id and current time to filter query on showw table
    shows_query = session.query(Show).join(Artist).with_entities(Show.artist_id, Artist.name, Artist.image_link, Show.start_time).filter(Show.venue_id == venue_id).all()

    past_shows = list()
    upcoming_shows = list()

    shows_query_attributes = shows_query[0]._asdict().keys()

    for show in shows_query:
        shows_data = dict()
        for attribute in shows_query_attributes:
            if attribute in ['name', 'image_link']:
                shows_data['artist_' + attribute] = show._asdict()[attribute]
            else:
                shows_data[attribute] = show._asdict()[attribute]

        if show.start_time > current_time:
            upcoming_shows.append(shows_data)
        else:
            past_shows.append(shows_data)


    data = venue[0]._asdict()

    # parse returned data dictionary
    data['past_shows'] = past_shows
    data['past_shows_count'] = len(past_shows)

    data['upcoming_shows'] = upcoming_shows
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


    # parse the entry of the venue table
    data = dict()
    venue_table_attributes = inspect(Venue).c
    for attribute in venue_table_attributes:
        if attribute.name == 'genres':
            data[attribute.name] = request.form.getlist(attribute.name)
        elif attribute.name == 'seeking_talent':
            data[attribute.name] = bool(request.form[attribute.name])
        else:
            data[attribute.name] = request.form[attribute.name]

    try:
        venue = Venue(**data)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + data['name'] + ' was successfully listed!')

    except Exception as error:
        # rollback pending changes on error
        db.session.rollback()
        flash('An error occurred. Venue ' + data['name'] + ' could not be listed.')

    finally:
        # close current session
        db.session.close()

    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  try:
    # retrieve entry of the venue table by input venue_id and delete it
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash(f'Venue {venue_id} was successfully deleted.')

  except Exception as error:
    # rollback pending changes on error
    db.session.rollback()
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')

  finally:
    # close curent session
    db.session.close()

  return None

'''
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None
'''

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  # retrieve all entries in artist table
  artists_data = db.session.query(Artist).with_entities(Artist.id, Artist.name).all()
  data =  [{'id': artist.id, 'name': artist.name} for artist in artists_data]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # parse search term and use it for filter the query
  search_term = request.form.get('search_term', '')
  artists_search_result = db.session.query(Artist).filter(Artist.name.like(f'%{search_term}%')).all()
  response = dict()
  response['count'] = len(artists_search_result)
  data = list()
  current_time = datetime.now()

  # loop over all search results from returned query and append it to list
  for artist in artists_search_result:
      artist_response = dict()
      artist_response['id'], artist_response['name'] = venue.id, venue.name
      upcoming_shows = db.session.query(Show).filter(and_(Show.artist_id == artist.id, Show.start_time > current_time)).all()
      artist_response['num_upcoming_shows'] = len(upcoming_shows)
      data.append(artist_response)

  # parse response dictionary
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    # query artist table by input artist_id
    # query venues table by input venue_id
    artist_table_attributes = inspect(Artist).c
    attribute_list = [attribute.name for attribute in artist_table_attributes]

    artist = db.session.query(Artist).with_entities(*attribute_list).filter(Artist.id == artist_id).all()
    shows_query = db.session.query(Show).join(Venue).with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(Show.artist_id == artist_id).all()
    current_time = datetime.now()

    data = dict()

    data = artist[0]._asdict()

    shows_query_attributes = shows_query[0]._asdict().keys()

    past_shows = list()
    upcoming_shows = list()

    for show in shows_query:
        shows_data = dict()
        for attribute in shows_query_attributes:
            if attribute == 'start_time':
                shows_data[attribute] = show._asdict()[attribute]
            else:
                shows_data['venue_' + attribute] = show._asdict()[attribute]

        if show.start_time > current_time:
            upcoming_shows.append(shows_data)
        else:
            past_shows.append(shows_data)

    data['past_shows'] = past_shows
    data['past_shows_count'] = len(past_shows)

    data['upcoming_shows'] = upcoming_shows
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  form = ArtistForm()

  artist_table_attributes = inspect(Artist).c
  attribute_list = [attribute.name for attribute in artist_table_attributes]

  artist = db.session.query(Artist).with_entities(*attribute_list).filter(Artist.id == artist_id).all()
  artist = artist[0]._asdict()

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  # retrieve artist record from artist table with input artist_id
  artist_table_attributes = inspect(Artist).c
  attribute_list = [attribute.name for attribute in artist_table_attributes]
  try:

      artist = db.session.query(Artist).with_entities(*attribute_list).filter(Artist.id == artist_id).all()
      artist = artist[0]._asdict()
      # update existing record attributes with input values from submitted form by assigning it to retrieved ORM object
      for attribute in artist_table_attributes:
        if attribute == 'genres':
            artist[attribute] = request.form.getlist(attribute)
        elif attribute == 'seeking_talent':
            artist[attribute] = bool(request.form[attribute])
        else:
            artist[attribute] = request.form[attribute]

      db.session.query(Artist).filter(Artist.id == artist_id).update(artist, synchronize_session="fetch")
      # commit ORM object changes to database
      db.session.commit()
  except Exception as error:
      # rollback pending changes on error
      db.session.rollback()


  finally:
    # close current session and parse submission message
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # populate form with fields from venue with ID <venue_id>
  form = VenueForm()

  venue_table_attributes = inspect(Venue).c
  attribute_list = [attribute.name for attribute in venue_table_attributes]

  venue = db.session.query(Venue).with_entities(*attribute_list).filter(Venue.id == venue_id).all()
  venue = venue[0]._asdict()

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    venue_table_attributes = inspect(Venue).c
    attribute_list = [attribute.name for attribute in venue_table_attributes]
    try:

        venue = db.session.query(Venue).with_entities(*attribute_list).filter(Venue.id == venue_id).all()
        venue = venue[0]._asdict()
        # update existing record attributes with input values from submitted form by assigning it to retrieved ORM object
        for attribute in venue_table_attributes:
          if attribute == 'genres':
              venue[attribute] = request.form.getlist(attribute)
          elif attribute == 'seeking_talent':
              venue[attribute] = bool(request.form[attribute])
          else:
              venue[attribute] = request.form[attribute]

        db.session.query(Venue).filter(Venue.id == venue_id).update(venue, synchronize_session="fetch")
        # commit ORM object changes to database
        db.session.commit()
    except Exception as error:
        # rollback pending changes on error
        db.session.rollback()

    finally:
      # close current session and parse submission message
      db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

    artist_table_attributes = inspect(Artist).c
    attribute_list = [attribute.name for attribute in artist_table_attributes]
    try:

        artist = db.session.query(Artist).with_entities(*attribute_list).filter(Artist.id == artist_id).all()
        artist = artist[0]._asdict()
        # update existing record attributes with input values from submitted form by assigning it to retrieved ORM object
        for attribute in artist_table_attributes:
          if attribute == 'genres':
              artist[attribute] = request.form.getlist(attribute)
          elif attribute == 'seeking_talent':
              artist[attribute] = bool(request.form[attribute])
          else:
              artist[attribute] = request.form[attribute]

        artist = Artist(**artist)

        db.session.add(artist)
        # commit ORM object changes to database
        db.session.commit()
    except Exception as error:
        # rollback pending changes on error
        db.session.rollback()

    finally:
      # close current session and parse submission message
      db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # perform left joins on show table with other tables to get info about all shows
  shows_query = db.session.query(Show).join(Artist).join(Venue).with_entities(Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time).all()

  data = []

  # loop over retrieved shows info and append data from ORM object to list
  for show in shows_query:
    data.append(show._asdict())

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  try:
    # assign submitted values to attributes
    form_data = dict()
    form_data['artist_id'] = request.form['artist_id']
    form_data['venue_id'] = request.form['venue_id']
    form_data['start_time'] = request.form['start_time']


    # parse the entry from submitted values by creating an ORM object then insert it to database
    show = Show(**form_data)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as error:
    # rollback pending changes on error
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    # close curent session
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
