import boto.ses
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import schedule
import time

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

with open('config.json') as json_file:  
    data = json.load(json_file)
    AWS_ACCESS_KEY = data['AWSAccessKey']
    AWS_SECRET_KEY = data['AWSSecretKey']
    YELP_API_KEY = data['Yelp_API_Key']


# Yelp API, this portion of code used this link as reference
# Ref: https://github.com/Yelp/yelp-fusion/blob/master/fusion/python/sample.py
class Yelp(object):
    def __init__(self):
        self.api_host = 'https://api.yelp.com'
        self.search_path = '/v3/businesses/search'

    def request(self, host, path, url_params=None):
        url_params = url_params or {}
        url = '{0}{1}'.format(host, quote(path.encode('utf8')))
        headers = {
            'Authorization': 'Bearer %s' % YELP_API_KEY,
        }

        print(u'Querying Yelp {0} ...'.format(url))
        response = requests.request('GET', url, headers=headers, params=url_params)
        return response.json()

    def search(self, term, location, limit, offset):
        url_params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'limit': limit,
            'offset': offset
        }
        return self.request(self.api_host, self.search_path, url_params=url_params)


# Email class
# Ref: http://stackabuse.com/how-to-send-an-email-with-boto-and-ses/
class Email(object):  
    def __init__(self, to, subject):
        self.to = to
        self.subject = subject
        self._html = None
        self._text = None
        self._format = 'html'

    def html(self, html):
        self._html = html

    def text(self, text):
        self._text = text

    def send(self, from_addr=None):
        body = self._html

        if isinstance(self.to, basestring):
            self.to = [self.to]
        if not from_addr:
            from_addr = 'mesorandeee@gmail.com'
        if not self._html and not self._text:
            raise Exception('You must provide a text or html body.')
        if not self._html:
            self._format = 'text'
            body = self._text

        connection = boto.ses.connect_to_region(
            # Oregon
            'us-west-2',
            aws_access_key_id=AWS_ACCESS_KEY, 
            aws_secret_access_key=AWS_SECRET_KEY
        )

        return connection.send_email(
            "mesorandeee@gmail.com",
            self.subject,
            None,
            self.to,
            format=self._format,
            text_body=self._text,
            html_body=self._html
        )


# EmailMe Class
# This class forms the Email by creating the HTML from the different API requests
class EmailMe(object):
    def __init__(self):
        self.htmlTextToSend = ""

    def startInterval(self):
        # Every day at 10:00PM
        schedule.every().day.at("22:00").do(self.sendEmail)
        while True:
            schedule.run_pending()
            time.sleep(60) # wait one minute

    def createSpotifyHTML(self, results, SpotifyOffset):
        spotifyHTML = ''
        for i, t in enumerate(results['albums']['items']):
            artists = ''
            first = True
            for artist in t['artists']:
                if first:
                    artists += artist['name'].encode('utf-8')
                    first = False
                else:
                    artists += ', ' + artist['name'].encode('utf-8')
            print i + SpotifyOffset, t['name'].encode('utf-8'), artists ,t['uri'].encode('utf-8')
            lineText = '<h3>' + str(i + SpotifyOffset) + '.) ' + t['name'].encode('utf-8') + '<br>'
            artistText = artists + '</h3>'
            imageCovers = '<img src=\"' + t['images'][1]['url'].encode('utf-8') + '\"><br>'
            uri = '<h3>' + t['uri'].encode('utf-8') + '</h3>'
            spotifyHTML += lineText + artistText + uri + imageCovers + '<br><br>'  #"%4d %s %s" % (i + 1, t['uri'],  t['name'])
        print('\n')
        return spotifyHTML

    def createYelpHTML(self, results, YelpOffset):
        yelpHTML = ''
        for i, t in enumerate(results['businesses']):
            lineText = '<h3>' + str(i + YelpOffset) + '.) ' + t['name'] + '<br>'
            rating = 'Rating: ' + str(t['rating'])
            location = t['location']['display_address'][0] + '<br>' + t['location']['display_address'][1] + '<br>'
            url = t['url']
            yelpHTML = lineText + rating + location + url + '<br><br>'
            print(yelpHTML)
        print('\n')
        return yelpHTML

    def sendEmail(self):
        with open('config.json') as json_file:  
            data = json.load(json_file)
            SPOTIFYID = data['SpotifyID']
            SPOTIFYSECRET = data['SpotifySecret']
            SpotifyOffset = data['SpotifyOffset']
            YelpOffset = data['YelpOffset']

        # Spotify
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFYID, client_secret=SPOTIFYSECRET)
        Spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        SpotifyResults = Spotify.new_releases(country='US', limit=1, offset=SpotifyOffset)
        print 'Querying Spotify New Releases'
        
        # Yelp
        YelpObj = Yelp()
        YelpResults = YelpObj.search("breweries", "Los Angeles", 1, YelpOffset)

        # Construct the HTML to send
        self.htmlTextToSend += '<html><body>'
        self.htmlTextToSend += self.createSpotifyHTML(SpotifyResults, SpotifyOffset)
        self.htmlTextToSend += self.createYelpHTML(YelpResults, YelpOffset)
        self.htmlTextToSend += '</body></html><br><br>' + 'Randy is awesome'

        # Send email
        # email = Email(to='randtru@gmail.com', subject='Ran\'z Email Update')  
        # email.html(self.htmlTextToSend)  # Optional  
        # email.send()  

        # Reset the offset if it reaches max offet, otherwise continue to increment the offset
        if SpotifyOffset >= 20:
            SpotifyOffset = 0
        else:
            SpotifyOffset += 1

        if YelpOffset >= 100:
            YelpOffset = 0
        else:
            YelpOffset += 1

        # Write the updated offset into the config
        with open('config.json', 'r+') as json_file:
            data = json.load(json_file)

            data['SpotifyOffset'] = SpotifyOffset
            data['YelpOffset'] = YelpOffset

            json_file.seek(0)
            json.dump(data, json_file, indent=4)
            json_file.truncate()


if __name__ == "__main__":
    app = EmailMe()
    # app.startInterval()
    app.sendEmail()

