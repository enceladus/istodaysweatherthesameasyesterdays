import urllib, re, simplejson

GEOCODE_BASE_URL = 'http://maps.googleapis.com/maps/api/geocode/json'
json = simplejson.JSONEncoder()

def find_between(s, first, last):
  try:
    start = s.index( first ) + len( first )
    end = s.index( last, start )
    return s[start:end]
  except ValueError:
    return ""

def remove_numbers(s):
  return re.sub('[0-9 ]+', '', s)

def geocode(address,sensor="false", **geo_args):
  geo_args.update({
    'address': address,
    'sensor': sensor  
  })

  url = GEOCODE_BASE_URL + '?' + urllib.urlencode(geo_args)
  result = simplejson.load(urllib.urlopen(url))

  return json.encode([s['formatted_address'] for s in result['results']])

if __name__ == '__main__':
  print geocode(address=55010,sensor="false")