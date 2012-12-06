import urllib, urllib2, re, simplejson

WWO_BASE_URL = 'http://free.worldweatheronline.com/feed/weather.ashx?'
GEOCODE_BASE_URL = 'http://maps.googleapis.com/maps/api/geocode/json'

def any_in_string(s, array):
	return any([x in s for x in array])

def find_between(s, first, last):
	""" Returns string between two subtrings """
	try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
	except ValueError:
			return ""

def remove_numbers(s):
	return re.sub('[0-9]+', '', s).strip()

def get_json(url):
	print url
	req = urllib2.Request(url)
	opener = urllib2.build_opener()
	f = opener.open(req)
	return simplejson.load(f)

def geocode(address, sensor="false", **geo_args):
	""" Returns a city name for an address/zipcode/search """

	json = simplejson.JSONEncoder()

	geo_args.update({
			'address': address,
			'sensor': sensor  
	})

	url = GEOCODE_BASE_URL + '?' + urllib.urlencode(geo_args)
	result = simplejson.load(urllib.urlopen(url))

	return json.encode([s['formatted_address'] for s in result['results']])