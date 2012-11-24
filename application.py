from flask import Flask, render_template, request, make_response

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


def celsius(fahrenheit):
	return (fahrenheit - 32) * 5/9

def yesterdays_weather(location):
	high = 55
	low = 44
	conditions = 'clear'
	return Weather(high, low, conditions)

def todays_weather(location):
	high = 33
	low = 22
	conditions = 'snow'
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