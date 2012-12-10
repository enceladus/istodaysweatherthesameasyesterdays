from application import *

zipcode = 78705
city = get_city_name(zipcode)

def w(city=city):
	return get_todays_weather(city)

def y(city=city, zipcode=zipcode):
	return get_yesterdays_weather(city, zipcode)

def c(zipcode=zipcode):
	return get_relative_weather(zipcode)

