#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# DONE: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(150))
    phone = db.Column(db.String(120))
    genres = db.Column((db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def _repr_(self):
      return f'< Venue {self.id} {self.name} {self.city}>'

    # DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))

    shows = db.relationship('Show', backref='artist', lazy=True)

    def _repr_(self):
      return f'< Artist {self.id} {self.name} {self.city}>'

      
    # DONE: implement any missing fields, as a database migration using Flask-Migrate

# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.today(), nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'

    # DONE: implement any missing fields, as a database migration using Flask-Migrate

# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # date = dateutil.parser.parse(value)
  if isinstance(value, str):
        date = dateutil.parser.parse(value)
  else:
        date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


# ---------------------------------------------------------------------------#
#  Functions For Search Implementation
# ---------------------------------------------------------------------------#
def search_item(query_table, val):
  search_term = request.form.get('search_term', '')
  items = db.session.query(query_table).filter(query_table.name.ilike(f'%{search_term}%')).all()
  num_items = len(items)

  search_result = {
    "count": num_items,
    "data": items,
  }
  if val == 1:
    return search_result
  elif val == 2:
    return search_term

# ---------------------------------------------------------------------------#
# Get cities and states without duplicate
# ---------------------------------------------------------------------------#
def city_state_no_duplicate(table1_name, table2_name):
  places = db.session.query(table1_name.city, table1_name.state).distinct(table1_name.city, table1_name.state).all()
  city_state = []
  venue_params = []

  for place in places:
    result = table1_name.query.filter(table1_name.state == place.state).filter(table1_name.city == place.city).all()

    for params in result:
      venue_params.append({
        "id": params.id,
        "name": params.name,
        "num_upcoming_shows": len(db.session.query(table2_name).filter(table2_name.start_time > datetime.now()).all())
      })

      city_state.append({
        "city": place.city,
        "state": place.state,
        "venues": venue_params,
      })
  return city_state

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # DONE: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  # To get cities and states and avoid duplicates

  return render_template('pages/venues.html', areas=city_state_no_duplicate(Venue, Show))


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  return render_template('pages/search_venues.html', results=search_item(Venue, 1), search_term=search_item(Venue, 2))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  artist_past_venues = db.session.query(Show).filter(Show.start_time < datetime.now(), Show.venue_id == venue_id).join(Artist, Show.venue_id == Artist.id).add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time).all()

  artist_upcoming_venues = db.session.query(Show).filter(Show.start_time > datetime.now(), Show.venue_id == venue_id).join(Artist, Show.venue_id == Artist.id).add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time).all()

  venue_details = Venue.query.filter(Venue.id == venue_id).first()

  past = []

  upcomings = []

  for show in artist_past_venues:
    past.append({
      "artist_id": show[1],
      "artist_name": show[2],
      "artist_image_link": show[3],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M"),
    })

  for upcoming in artist_upcoming_venues:
      upcomings.append({
      "artist_id": upcoming[1],
      "artist_name": upcoming[2],
      "artist_image_link": upcoming[3],
      "start_time": upcoming.start_time.strftime("%m/%d/%Y, %H:%M"),
      })

  data = {
              "id": venue_details.id,
              "name": venue_details.name,
              "genres": venue_details.genres,
              "address":venue_details.address,
              "city": venue_details.city,
              "state": venue_details.state,
              "phone": venue_details.phone,
              "website": venue_details.website_link,
              "facebook_link": venue_details.facebook_link,
              "seeking_talent": venue_details.seeking_talent,
              "seeking_description": venue_details.seeking_description,
              "image_link": venue_details.image_link,
              "past_shows": past,
              "upcoming_shows": upcomings,
              "past_shows_count": len(artist_past_venues),
              "upcoming_shows_count": len(artist_upcoming_venues),
            }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  form = VenueForm(request.form)
  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
  
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,
                    image_link=image_link, facebook_link=facebook_link, website_link=website_link,
                    seeking_talent=seeking_talent, seeking_description=seeking_description)
    try:
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      print(sys.exc_info())
      db.session.rollback()
      flash('An error occurred. ' + request.form['name'] + ' Venue could not be listed.')
    finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  return render_template('pages/search_artists.html', results=search_item(Artist, 1), search_term=search_item(Artist, 2))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # DONE: replace with real artist data from the artist table, using artist_id
  
  artist_past_shows = db.session.query(Show).filter(Show.start_time < datetime.now(), Show.artist_id == artist_id).join(Venue, Show.artist_id == Venue.id).add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time).all()

  artist_upcoming_shows = db.session.query(Show).filter(Show.start_time > datetime.now(), Show.artist_id == artist_id).join(Venue, Show.artist_id == Venue.id).add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time).all()

  artist_details = Artist.query.filter(Artist.id == artist_id).first()

  past = []

  upcomings = []

  for show in artist_past_shows:
    past.append({
      "venue_id": show[1],
      "venue_name": show[2],
      "venue_image_link": show[3],
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M"),
    })

  for upcoming in artist_upcoming_shows:
      upcomings.append({
      "venue_id": upcoming[1],
      "venue_name": upcoming[2],
      "venue_image_link": upcoming[3],
      "start_time": upcoming.start_time.strftime("%m/%d/%Y, %H:%M"),
      })

  data = {
              "id": artist_details.id,
              "name": artist_details.name,
              "genres": artist_details.genres,
              "city": artist_details.city,
              "state": artist_details.state,
              "phone": artist_details.phone,
              "website": artist_details.website_link,
              "facebook_link": artist_details.facebook_link,
              "seeking_venue": artist_details.seeking_venue,
              "seeking_description": artist_details.seeking_description,
              "image_link": artist_details.image_link,
              "past_shows": past,
              "upcoming_shows": upcomings,
              "past_shows_count": len(artist_past_shows),
              "upcoming_shows_count": len(artist_upcoming_shows),
            }
  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
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
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  form = ArtistForm(request.form)
  if form.validate():
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
  
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres,
                    image_link=image_link, facebook_link=facebook_link, website_link=website_link,
                    seeking_venue=seeking_venue, seeking_description=seeking_description)
    try:
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      print(sys.exc_info())
      db.session.rollback()
      flash('An error occurred. ' + request.form['name'] + ' Artist could not be listed.')
    finally:
      db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  list_of_shows = Show.query.join(Venue, Venue.id == Show.venue_id).join(Artist, Artist.id == Show.artist_id).all()
  def get_list_of_shows(list_param):
      shows = []
      for show in list_param:
        #Push multiple elements into an array
        shows.append(
          {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time),
          }
        )
      return shows
  
  return render_template('pages/shows.html', shows=get_list_of_shows(list_of_shows))

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead

  form = ShowForm(request.form)
  if form.validate():
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
  
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    try:
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    except:
      print(sys.exc_info())
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
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
