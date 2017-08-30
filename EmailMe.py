import boto.ses
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import schedule
import time

with open('config.json') as json_file:  
        data = json.load(json_file)
        AWS_ACCESS_KEY = data['AWSAccessKey']
        AWS_SECRET_KEY = data['AWSSecretKey']
        SPOTIFYID = data['SpotifyID']
        SPOTIFYSECRET = data['SpotifySecret']
        SpotifyOffset = data['SpotifyOffset']

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
            from_addr = 'me@example.com'
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


def sendEmail(t):
    with open('config.json') as json_file:  
        data = json.load(json_file)
        AWS_ACCESS_KEY = data['AWSAccessKey']
        AWS_SECRET_KEY = data['AWSSecretKey']
        SPOTIFYID = data['SpotifyID']
        SPOTIFYSECRET = data['SpotifySecret']
        SpotifyOffset = data['SpotifyOffset']

    # Spotify
    client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFYID, client_secret=SPOTIFYSECRET)
    Spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    results = Spotify.new_releases(country='US', limit=5, offset=SpotifyOffset)

    htmlTextToSend = '<html><body>'
    for i, t in enumerate(results['albums']['items']):
        artists = ''
        first = True
        for artist in t['artists']:
            if first:
                artists += artist['name']
                first = False
            else:
                artists += ', ' + artist['name']
        print i + 1, t['name'], artists ,t['uri']
        lineText = '<h3>' + str(i + 1) + '.) ' + t['name'] + '<br>'
        artistText = artists + '</h3>'
        imageCovers = '<img src=\"' + t['images'][1]['url'] + '\"><br>'
        uri = '<h3>' + t['uri'] + '</h3>'
        htmlTextToSend += lineText + artistText + uri + imageCovers + '<br><br>'  #"%4d %s %s" % (i + 1, t['uri'],  t['name'])
    htmlTextToSend += '</body></html><br><br>' + 'Randy is awesome'

    # Send email
    email = Email(to='randtru@gmail.com', subject='Ran\'z Email Update')  
    email.html(htmlTextToSend)  # Optional  
    email.send()  

    # Reset the offset if it reaches max offet, otherwise continue to increment the offset
    if SpotifyOffset >= 500:
        SpotifyOffset = 0
    else:
        SpotifyOffset += 5
    # Write the updated offset into the config
    with open('config.json', 'r+') as json_file:
        data = json.load(json_file)

        data['SpotifyOffset'] = SpotifyOffset

        json_file.seek(0)
        json.dump(data, json_file, indent=4)
        json_file.truncate()
    
    return

# schedule.every().day.at("22:27").do(sendEmail,'')

# while True:
#     schedule.run_pending()
#     time.sleep(60) # wait one minute

sendEmail(1)
