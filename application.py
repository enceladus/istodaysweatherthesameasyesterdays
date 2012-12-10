from __future__ import with_statement
from flask import Flask, render_template, request, make_response
import urllib2, simplejson, sqlite3, keys, sys, json
from urllib import urlencode
from contextlib import closing
from datetime import date, timedelta
from flask.ext.sqlalchemy import SQLAlchemy
from app_utils import *

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = keys.DATABASE_URI
db = SQLAlchemy(app)


# The flow of the app:
# 1. Zipcode request resolves to city name - get_city_name(zipcode)
#   a. If that fails, break w/ error message, show sample (Austin, TX)
# 2. Get yesterday's weather - yesterdays_weather(city)
#   a. First from db
#   b. If that fails, fetch from wunderground api - get_json(url)
#   c. If that fails, break w/ error message
# 3. Get today's weather - todays_weather(city)
#   a. First from db
#   b. If that fails, fetch from worldweatheronline api - get_json(url)
#   c. If that fails, break w/ error message
# 4. Compare two Weather objects - compare(today, yesterday)
#   a. standardize_description()
# 5. All of this wrapped in get_relative_weather(zipcode)

# get_weather_from_database and get_weather_from_api should BOTH
# return Weather objects, with high, low, avg, and condition attributes

def get_relative_weather(zipcode):
  try:
    city = get_city_name(zipcode)
  except:
    print 'Error!'
    return False

  yesterday = get_yesterdays_weather(city, zipcode)
  today = get_todays_weather(city)
  return (today, yesterday, compare(today, yesterday))

def get_city_name(zipcode):
  """ Gets city name from a zipcode using Google Maps API
    Returns in format City, ST, Country """
  try:
    city = geocode(zipcode)
    city = find_between(city, '"', '"')   # remove json formatting
    city = city.split(', ')               # separate into parts
    city[1] = remove_numbers(city[1])
    return ', '.join(city).strip()        # return final value
  except:
    print 'Your city was not found, resorting to default.'
    return 'Austin, TX, USA'              # show sample on break

def get_todays_weather(city):
  """ Fetches today's weather either from DB cache or API """

  print "-- Getting today's weather --"

  day = date.today()          # returns (YYYY, MM, DD)
  return get_weather_from_database(city, day) or get_weather_from_api(city, 'today')

def get_yesterdays_weather(city, zipcode):
  """ Fetches yesterday's weather either from DB cache or API """

  print "-- Getting yesterday's weather --"
  day = date.today() - timedelta(1)     # returns (YYYY, MM, DD-1)
  return get_weather_from_database(city, day) or get_weather_from_api(city, 'yesterday', zipcode)

def get_weather_from_database(city, day):
  """ Gets weather object from DB for specified city and date """

  print "... trying in the database"
  try:
    weather = Weather.query.filter_by(city=city, day=day).first()
    weather.avg = (weather.high + weather.low) / 2
  except:
    weather = None
  if weather == None: print '... record could not be found.'
  return weather

def get_weather_from_api(city, day, zipcode=None):
  """ fetches weather from either WWO or WU """

  print "... trying the API"
  if day == 'today':
    try:
      data = {'q': city, 'format': 'json', 'key': keys.WWO_API_KEY}
      weather_json = get_json(WWO_BASE_URL + urllib.urlencode(data))
      high = int(weather_json['data']['weather'][0]['tempMaxF'])
      low = int(weather_json['data']['weather'][0]['tempMinF'])
      conditions = standardize_description('wwo', weather_json['data']['weather'][0]['weatherDesc'][0]['value'])
      weather = Weather(city, high, low, conditions, date.today())
      print '... weather fetched from API.'
    except:
      weather = None
  elif day == 'yesterday':
    try:
      f = urllib2.urlopen("{0}yesterday/q/{1}.json".format(keys.WU_BASE_URL, zipcode))
      json_string = f.read()
      parsed_json = json.loads(json_string)
      summary = parsed_json['history']['dailysummary'][0]
      high = int(summary['maxtempi'])
      low = int(summary['mintempi'])
      conditions = standardize_description('wu', summary)
      f.close()
      weather = Weather(city, high, low, conditions, date.today() - timedelta(1))
      print '... weather fetched from API.'
    except:
      print '... weather could not be fetched from API. Probably an international zipcode.'
      return False
  return weather

class Weather(db.Model):
  """ Stores weather information from the API,
    also serves as a model for the database. """

  id = db.Column(db.Integer, primary_key=True)
  city = db.Column(db.String(150))
  high = db.Column(db.Integer)
  low = db.Column(db.Integer)
  conditions = db.Column(db.String(80))
  day = db.Column(db.Date)
  
  def __init__(self, city, high, low, conditions, day):
    self.city     = city
    self.high     = high
    self.low      = low
    self.conditions = conditions
    self.day    = day
    self.avg    = (high + low) / 2
    self.save()

  def __repr__(self):
    return "<Weather {0}>".format(self.city)

  def hotter_than(self, other):
    return (self.avg > other.avg + 4)

  def colder_than(self, other):
    return (self.avg < other.avg - 4)

  def save(self):
    try:
      if get_weather_from_database(self.city, self.day):
        print '... already in database. no need to save again.'
        return True
      else:
        print '... saving in database'
        db.session.add(self)
        db.session.commit()
    except:
      print '... could not be saved to database.'
      return False

def standardize_description(api, description):
  """ Standardizes description to one of the following: clear, clouds, storm, freezing, snow, wet """
  # based on codes from 
  # http://www.worldweatheronline.com/feed/wwoConditionCodes.txt

  # World Weather Online
  if api == 'wwo':
    d = description.lower()
    conditions = {
         'clear':   ['clear', 'sunny'],
        'clouds':   ['cloudy', 'overcast', 'fog'],
         'storm':   ['thunder'],
      'freezing':   ['ice', 'sleet', 'freezing rain', 'freezing drizzle'],
          'snow':   ['snow', 'blizzard'],
           'wet':   ['rain', 'drizzle', 'mist']
    }

    for key in conditions.keys():
      if any_in_string(d, conditions[key]):
        return key
    return 'other'

  # Weather Underground
  elif api == 'wu':
    fog = bool(int(description['fog']))
    wet = bool(int(description['rain']))
    snow = bool(int(description['snow']))
    freezing = bool(int(description['hail']))
    storm = bool(int(description['thunder'])) or bool(int(description['tornado']))
    if storm: return 'storm'
    if snow: return 'snow'
    if freezing: return 'freezing'
    if wet: return 'wet'
    return 'clear'

  print '... failed to standardize description'
  return False



def compare(today, yesterday):

  result = ""

  if not (today and yesterday):
    print '... cannot compare. Quitting.'
    return False

  if today.hotter_than(yesterday):
    result = "No, it's hotter"
  elif today.colder_than(yesterday):
    result = "No, it's colder"
  else:
    result = "It's about the same"

  if today.conditions != yesterday.conditions:
    if result[:2] == "No":
      result += " and "
    else:
      result += " but "

    if today.conditions == 'wet':
      result += "it's raining (boo)"
    elif today.conditions == 'clear':
      result += "it's clear (woo!)"
    elif today.conditions == 'snow':
      result += "it's snowing!"
    else:
      result += "the sky looks different"

  return result

def default_zipcode():
  zipcode = request.cookies.get('zipcode')
  if zipcode is None:
    zipcode = 78705
  return zipcode

@app.route('/')
def index(zipcode=None):
  """ The only page there is """

  zipcode = request.args.get('zipcode') or default_zipcode()

  if (zipcode != default_zipcode()):
    new_zipcode = request.args.get('zipcode')
    today, yesterday, weather = get_relative_weather(new_zipcode)

    resp = make_response(render_template('index.html', 
      today=today,
      yesterday=yesterday,
      weather=weather, 
      zipcode=new_zipcode))
    resp.set_cookie('zipcode', new_zipcode)
    return resp

  today, yesterday, weather = get_relative_weather(zipcode)
  return render_template('index.html', 
    today=today,
    yesterday=yesterday,
    weather=weather, 
    zipcode=zipcode)

if __name__ == '__main__':
  app.run(port=8000)