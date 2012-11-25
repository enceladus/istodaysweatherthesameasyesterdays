Is Today's Weather the Same as Yesterday's?
==================================

It's a webapp to answer that basic question. Written in Flask.

Here's how it will work:

1. When you visit the site, it will attempt to use HTML5 geolocation to get your latitude and longitude.
2. If that doesn't work, you can manually type in a zipcode or city name.
3. It resolves lat/long and zipcodes to city names.
4. If the data for that city has been requested from the weather API already today, you are served cached data. Otherwise, the data will be requested from the API.
5. If the data for that city was requested _yesterday_, you are served that cached data. Otherwise, the data will be requested.
6. Each new day, all of the cached data for "today" is moved to "yesterday" in the database.

The database doesn't store entire forecasts and weather profiles, just:
 + The city name
 + Maximum/minimum temperatures in Fahrenheit
 + Weather condition: "clear", "rain", "storms", etc.

Sample responses to the titular question:
 + "No, it's warmer today."
 + "Yep, pretty much the same."
 + "No, it's colder...and snowing!"
 + "It's still raining, but today it's a little colder."

We'll see how that works out.