mport os
import functools
import json
import sys
import urllib
import webbrowser
import uuid
import gevent
import base64
import datetime
import requests
import pkce
from urllib.parse import urlencode
import urllib.parse as urlparse
from urllib.parse import parse_qs
from gevent.pywsgi import WSGIServer
from json.decoder import JSONDecodeError
from flask import Flask
from flask import (Blueprint, Flask, flash, g, redirect, render_template,request, session, url_for)

#Program: Smart Shuffle
#Author: Steve Berg
#Last Updated: Jan 12, 2021
#Date Created: Jan 5, 2021
#Purpose: A web-based app that processes and reorders a given Spotify Playlist, determined by feature analysis from Spotify's web API

#For the purpose of this repo, dev credentials and redirect uri's are ommited from this file
#Class API for Spotify Web interaction
class SpotifyAPI(object):
    auth_refresh_token = None
    auth_access_token = None
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(self,client_id,client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs) #Calls any class that it is inherting from itself
        self.client_id = client_id
        self.client_secret = client_secret
        self.test_flag = False
    #Helper function to generate and send a request for client credentials for further useage
    def get_client_creds(self):
        """
        RETURNS A BASE64 ENCODED STRING
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    #Generates token headers for API endpoint referencing in base64 encoding
    def get_token_headers(self):
        client_creds_b64 = self.get_client_creds()
        return {"Authorization": f"Basic {client_creds_b64}"}
    
     #Generates client credential for API endpoint referencing in base64 encoding
    def get_token_data(self):
        return {"grant_type": "client_credentials"}

    #Performs authorization of the API given client details
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers = token_headers)
        if r.status_code not in range(200,299): 
            print("API Request Error: ",r.status_code)
            raise Exception("Could not authenticate client.")
        data = r.json()
        now = datetime.datetime.now()
        access_token  = data['access_token']
        expires_in = data['expires_in'] #seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True
    
    #Helper function that retrieves an access token for the client
    def get_access_token(self):
        auth_done = self.perform_auth()
        if not auth_done:
            raise Exception("Authentication failed")
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    #Refreshes the user access token grated via user authorization
    def refresh_user_access_token(self,refresh_token):
        token_url = self.token_url
        client_id = self.client_id
        query_params ={'grant_type':'refresh_token', 'refresh_token':refresh_token,'client_id': client_id}
        r = requests.post(token_url, data = query_params)
        if r.status_code not in range(200,299):
            print("Token Request Error: ",r.statu.s_code)
            print(r.json())
            return {}
        if r.status_code == 200:
            r_new = r.json()
            access_token = r_new.get('access_token')
            refresh_token = r_new.get('refresh_token')
            return access_token, refresh_token

    #Helper function that generates and returns a f-string for API endpoint requests, for an access token request 
    def get_access_header(self):
        access_token = self.get_access_token()
        headers = {"Authorization" : f"Bearer {access_token}"}
        return headers

    #Helper function that generates and returns a f-string for API endpoint requests, for an access token request 
    def get_auth_access_header(self):
        access_token = self.auth_access_token
        headers = {"Authorization" : f"Bearer {access_token}"}
        return headers
    
    #Sub-Routine that processes returned Web-API requests
    def process_request(self,request):
        if request.status_code not in range(200,299):
            print("API Request Error: ",request.status_code)
            return {}
        if request.status_code == 200:
            #parsed = urlparse.urlparse(self.requests.url)
            return request.json()
        else:
            print("Other authentification issue has occured: ",request.status_code)
            return {}
    
    #Fetches an album search result via Spotify search engine
    def get_album(self,_id):
        return self.get_resource(_id,resource_type = 'albums')

    #Helper function that fetches the resource type, via generating and sending a API endpoint request
    #Set as default to fetch album resource type
    def get_resource(self,lookup_id,resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint,headers=headers)
        if r.status_code() not in range(200,299):
            return {}
        return r.json()
    
    #The base search function for the API
    def base_search(self,query_params,search_type = 'artist'):
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/search"
        #data = urlencode({"q": query, "type": search_type.lower()})
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url,headers=headers)
        return self.process_request(r)

    #Search function that takes operator quesries and operators as parameters of the search
    def search(self,query=None,operator=None, operator_query=None,search_type = 'artist'):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query,dict):
            query = " ".join( [f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query !=None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query,str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query, "type": search_type.lower()})
        return self.base_search(query_params)
    
    #Helper function that fetches the user's list of playlists
    def get_user_playlist_list(self):
        headers = self.get_auth_access_header()
        endpoint = "https://api.spotify.com/v1/me/playlists"
        #endpoint = endpoint[:33] + client_user + endpoint[33:]
        r = requests.get(endpoint,headers=headers)
        return self.process_request(r)

    #Helper function that fetches a specific playlist given the id
    def get_playlist(self,playlist_name):
        playlist_id = playlist_name
        headers = self.get_auth_access_header()
        endpoint = "https://api.spotify.com/v1/playlists/"
        endpoint = endpoint[:38] + playlist_id + endpoint[38:]
        r = requests.get(endpoint,headers=headers)
        return self.process_request(r)

    #Helper function that fetches a specific playlist given the id
    def get_playlist_tracks(self,playlist_name):
        playlist_id = playlist_name
        headers = self.get_auth_access_header()
        endpoint = "https://api.spotify.com/v1/playlists//tracks"
        endpoint = endpoint[:37] + playlist_id + endpoint[37:]
        r = requests.get(endpoint,headers=headers)
        return self.process_request(r)
    
    #Helper function to execute an instance of a playlist reorder
    def playlist_reorder(self,playlist_name,range_start,range_length,insert_before,snapshot_id):
        playlist_id = playlist_name
        headers = self.get_auth_access_header()
        endpoint = "https://api.spotify.com/v1/playlists//tracks"
        endpoint = endpoint[:37] + playlist_id + endpoint[37:]
        if snapshot_id == None:
            query_params ={'range_start':range_start,'range_length':range_length,'insert_before':insert_before}
        else:
           query_params ={'range_start':range_start,'range_length':range_length,'insert_before':insert_before,'snapshot_id':snapshot_id} 
        r = requests.post(endpoint, data = query_params)
        if r.status_code not in range(200,299):
            print("Token Request Error: ",r.status_code)
            print(r.json())
            return {}
        if r.status_code == 200:
            r_new = r.json()
            self.auth_access_token = r_new.get('access_token')
            self.refresh_token = r_new.get('refresh_token')
            return True

    #Function that returns an object of audio features for a given list of tracks
    def extract_audio_features(self,ids):
        endpoint = 'https://api.spotify.com/v1/audio-features'
        headers = self.get_auth_access_header()
        id_string = ','.join(ids)
        query_params = {'ids':id_string}
        print(query_params)
        lookup_url = f"{endpoint}?{query_params}"
       # print(lookup_url)
        r = requests.get(endpoint,headers=headers,params=query_params)
        return self.process_request(r)

    #Function that retrieve's a list of the client's playlists
    def get_playlists(self):    #Create separte functions for playlist object parsing
        playlists = self.get_user_playlist_list()
        playlists = playlists['items']
        playlist =  self.get_playlist_tracks('2Jtpg8wTWunA1yHPwDbLQn') #Spotify_Id for 20th Bday playlist on Spotify Account
        tracklist = playlist['items']
        track_ids = []
        for tracks in tracklist:
            track = tracks['track']
            track_ids.append(track['id'])
        print(track_ids)    #Test code to check if print works
        return self.extract_audio_features(track_ids)

    #Helper function that fetches the displayed username of a client
    def get_username(self):
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/me"
        r = requests.get(endpoint,headers=headers)
        return self.process_request(r)
    
    #Helper function that sends a request for user authorization of data usage
    def get_auth_uri(self, client_id,code_challenge):
        endpoint = 'https://accounts.spotify.com/authorize'
        state = 'xyzABC123'
        query_params = urlencode({'client_id': client_id, 'response_type':'code','redirect_uri':redirect_uri,
                                 'code_challenge_method': 'S256', 'code_challenge': code_challenge,'state': state})
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url)
        if r.status_code not in range(200,299):
            print("API Request Error: ",r.status_code)
            return {}
        if r.status_code == 200: return r.url

    #Getting a user-authorized access token with a requested authorization code
    def get_user_access_token(self,client_id,code_verifier,code):
        endpoint = 'https://accounts.spotify.com/api/token'
        query_params ={'client_id': client_id, 'grant_type':'authorization_code','code': code,'redirect_uri': redirect_uri,'code_verifier': code_verifier}
        r = requests.post(endpoint, data = query_params)
        if r.status_code not in range(200,299):
            print("Token Request Error: ",r.statu.s_code)
            print(r.json())
            return {}
        if r.status_code == 200:
            r_new = r.json()
            self.auth_access_token = r_new.get('access_token')
            self.refresh_token = r_new.get('refresh_token')
            return True

#Flask app istelf that runs application
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    spotify_session = SpotifyAPI(dev_id,dev_secret_key)
    code_verifier = pkce.generate_code_verifier(length=128)
    code_challenge = pkce.get_code_challenge(code_verifier)
    test_flag = None
    app.config.from_mapping(
        SECRET_KEY='dev',
         #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'), Implement if using database system
    )

    from . import auth
    app.register_blueprint(auth.bp)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def home():
        spotify_session.perform_auth()
        res_url = spotify_session.get_auth_uri(dev_id,code_challenge)
        return redirect(res_url)

    @app.route('/test')
    def test():
        if(spotify_session.test_flag == False):
            code = request.args.get('code')
            state = request.args.get('state')
            print("Heres the code: ",code)
            print("Here's the state: ",state)
            spotify_session.test_flag = True
            spotify_session.get_user_access_token(dev_id,code_verifier,code)
            print("Here's the access token: ",spotify_session.access_token)
            print("Here's the refresh token: ",spotify_session.refresh_token)
            return spotify_session.get_playlists()
        #return redirect(url_for('auth.auth_for_token'))


    @app.route('/final')
    def final():
        return 'Hell yeah! :D'


    with app.test_request_context():
        print(url_for('auth.login_auth'))

    if __name__ == '__main__':
        app.run(debug=False)
        #app.run(host="0.0.0.0", port=5000, debug=True)

    return app
