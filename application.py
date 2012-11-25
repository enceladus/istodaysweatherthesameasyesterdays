from flask import Flask, render_template, request, make_response
import urllib2, simplejson
from urllib import urlencode

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)

class Weather:
	def __init__(self, high, low, conditions):
		self.high = high
		self.low = low
		self.avg = (high + low) / 2
		self.conditions = conditions

	def hotter_than(self, other):
		return (self.avg > other.avg + 4)

	def colder_than(self, other):
		return (self.avg < other.avg - 4)

def standardize_description(description):
	# based on codes from 
	# http://www.worldweatheronline.com/feed/wwoConditionCodes.txt

	# compare description
		# if contains 'clear' or 'sunny', return 'clear'
		# if contains 'cloudy', 'overcast', 'fog', return 'clouds'
		# if contains 'thunder', return 'storm'
		# if contains 'ice', 'sleet', 'freezing rain', 'freezing drizzle'
		# if contains 'snow', 'blizzard', 
		# if contains 'rain', 'drizzle', 'mist', return 'wet'
	return 0

def get_json(url):
	req = urllib2.Request(url)
	opener = urllib2.build_opener()
	f = opener.open(req)
	return simplejson.load(f)

def yesterdays_weather(location):
	weather_json = get_json('http://autocomplete.wunderground.com/aq?query=' + location)

	high = 55
	low = 44
	conditions = 'clear'
	return Weather(high, low, conditions)

def todays_weather(location):
	weather_json = get_json("http://free.worldweatheronline.com/feed/weather.ashx?q=" + location + "&format=json&key=6f0b244099202239122511")

	high = int(weather_json['data']['weather'][0]['tempMaxF'])
	low = int(weather_json['data']['weather'][0]['tempMinF'])
	# conditions = get_conditions_from_code(weather_json['data']['weather'][0]['weatherCode'])
	conditions = weather_json['data']['weather'][0]['weatherDesc'][0]['value']
	return Weather(high, low, conditions)

def compare(location):
	yesterday = yesterdays_weather(location)
	today = todays_weather(location)

	result = ""

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

		if today.conditions == 'rain':
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
	zipcode = request.args.get('zipcode') or default_zipcode()

	if (zipcode != default_zipcode()):
		new_zipcode = request.args.get('zipcode')
		resp = make_response(render_template('index.html', 
			today=todays_weather(zipcode),
			yesterday=yesterdays_weather(zipcode),
			weather=compare(new_zipcode), 
			zipcode=new_zipcode))
		resp.set_cookie('zipcode', new_zipcode)
		return resp

	return render_template('index.html', 
		today=todays_weather(zipcode),
		yesterday=yesterdays_weather(zipcode),
		weather=compare(zipcode), 
		zipcode=zipcode)

if __name__ == '__main__':
	app.run(port=8000)