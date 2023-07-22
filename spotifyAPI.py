import base64
import datetime
import requests
from urllib.parse import urlencode
#Program: spotifyAPI.py
#Author: Steve Berg
#Last Updated: Mar 19, 2022
#Date Created: Jan 5, 2021
#Purpose: A web-based app that processes and reorders a given Spotify Playlist, determined by feature analysis from Spotify's web API
#Class API for Spotify Web interaction
#Utilizes Authorization Code Flow with PKCE
redirect_uri = 'http://127.0.0.1:5000/smartplaylist'

class SpotifyAPI(object):
    auth_refresh_token = None
    auth_access_token = None
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    playlist = None
    newname = None
    auth_state = None
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(self,client_id,client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs) #Calls any class that it is inherting from itself
        self.client_id = client_id
        self.client_secret = client_secret
        self.test_flag = False

#Authentication Functions:
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

    #Helper function that retrieves an access token for the client
    def get_access_token(self):
        auth_done = self.perform_auth()
        if not auth_done:
            raise Exception("Authentication failed")
        token = self.auth_access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    #Helper function that generates and returns a f-string for API endpoint requests, for an access token request 
    def get_access_header(self):
        token_info = self.refresh_user_access_token(self.auth_refresh_token)
        self.auth_refresh_token=token_info[1]
        headers = {"Authorization" : f"Bearer {token_info[0]}"}
        return headers

    #Sub-Routine that processes returned Web-API requests
    def process_request(self,request):
        if request.status_code not in range(200,299):
            print("API Request Error: ",request.status_code)
            return {}
        if request.status_code == 200 or request.status_code == 201:
            #parsed = urlparse.urlparse(self.requests.url)
            #print('Process request succeeded.\n')
            return request.json()
        else:
            print("Other authentification issue has occured: ",request.status_code)
            return request.json()

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
        access_token  = data.get('access_token')
        expires_in = data.get('expires_in') #seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.auth_access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        print('Spotify User Authentification Complete...')
        return True
    
    #Retrieve's client's Spotify User ID, using given Spotify username
    def get_client_id(self):
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/me"
        r = requests.get(endpoint,headers=headers)
        r = self.process_request(r)
        if 'error' in r:
            print("API Request Error: ",r.status)
            return {}
        else: 
            print("Client ID Fetched...")
            return r['display_name']

        #Retrieve's client's Spotify User ID, using given Spotify username
    def get_client_id_num(self):
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/me"
        r = requests.get(endpoint,headers=headers)
        r = self.process_request(r)
        if 'error' in r:
            print("API Request Error: ",r.status)
            return {}
        else: 
            print("Client ID Fetched...")
            return r['id']

    #Helper function that sends a request for user authorization of data usage
    #Constructing the authorization URI, Step #2
    def get_auth_uri(self,client_id,code_challenge):
        endpoint = 'https://accounts.spotify.com/authorize'
        state = 'xyzABC123'
        self.auth_state = state
        query_params = urlencode({'client_id': client_id, 'response_type':'code','redirect_uri':redirect_uri,
                                 'code_challenge_method': 'S256', 'code_challenge': code_challenge,'state': state,'scope':'playlist-modify-private playlist-modify-public playlist-read-private playlist-read-collaborative user-library-read'})
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url)
        if r.status_code not in range(200,299):
            print("API Request Error: ",r.status_code)
            return {}
        #Redirects user to auth URI, Step 3 in auth
        if r.status_code == 200: 
            print("Authorization URI Constructed...")
            return r.url

    #Getting a user-authorized access token with a requested authorization code
    #Step 4 in auth
    def get_user_access_token(self,client_id,code_verifier,code):
        endpoint = 'https://accounts.spotify.com/api/token'
        query_params ={'client_id': client_id, 'grant_type':'authorization_code','code': code,'redirect_uri': redirect_uri,'code_verifier': code_verifier}
        r = requests.post(endpoint, data = query_params)
        r_new = self.process_request(r)
        if r != {}:
            print('User Access Token Request Suceeded')
            self.auth_access_token = r_new.get('access_token')
            self.auth_refresh_token = r_new.get('refresh_token')
            return r.json()
        else:
            print("Error in User Access Token request...")
            return {}

    #Refreshes the user access token grated via user authorization
    #Step 6 in auth
    def refresh_user_access_token(self,refresh_token):
        token_url = self.token_url
        client_id = self.client_id
        query_params ={'grant_type':'refresh_token', 'refresh_token':refresh_token,'client_id': client_id}
        r = requests.post(token_url, data = query_params)
        r_new = self.process_request(r)
        if r_new != {}:
            print('User Access Token Refreshed...')
            access_token = r_new.get('access_token')
            refresh_token = r_new.get('refresh_token')
            return access_token, refresh_token
        else:   #If request is not valid JSON
            return None, None 
       

#Playlist Functions
    #Helper function that fetches the client list of playlists
    def get_client_playlists(self):
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/me/playlists"
        r = requests.get(endpoint,headers=headers)
        r = self.process_request(r)
        return r

    #Helper function that fetches a specific playlist given the Spotify id or 'Playlist Name'
    def get_playlist_tracks(self,playlist_name):
        print('Retriving tracklist of ',playlist_name,'...')
        headers = self.get_access_header()
        endpoint = "https://api.spotify.com/v1/playlists//tracks"
        endpoint = endpoint[:37] + playlist_name + endpoint[37:]
        r = requests.get(endpoint,headers=headers)
        res = self.process_request(r)
        master_res_list = []
        master_res_list.append(res)
        next_uri = res['next']
        if next_uri != None:
            endpoint = next_uri
            while res['next'] != None:
                r = requests.get(endpoint,headers=headers)
                res = self.process_request(r)
                master_res_list.append(res)
                endpoint = res['next']
        return master_res_list
    
  #Function that extract's Spotify song ID's from playlist, with flag specifying the type of add to conduct,1 indicating full url encoding format, and 0 for not
    def get_song_ids(self,playlist,flag):
        track_ids = []
        count = 0
        print('Extracting Spotify song-ids from playlist... ')
        for portion in playlist:
            for tracks in portion['items']:    #Parses Spotify track ID's from all playlist tracks
                track = tracks['track']
                if flag:
                    if track !=None and track['id']!= None: track_ids.append('spotify:track:'+track['id'])
                else:
                    if track !=None and track['id']!= None: track_ids.append(track['id'])
            count+=1
        print('Complete')
        return track_ids
        
    #Function that creates a playlist for the user
    def create_playlist(self,name):
        user_num = self.get_client_id_num()
        endpoint = 'https://api.spotify.com/v1/users//playlists'
        headers= self.get_access_header()
        endpoint = endpoint[:33] + user_num + endpoint[33:]
        query_params ={'name':name,'public':True}
        r = requests.post(endpoint,json=query_params,headers=headers)
        if r.status_code not in range(200,299):
            print("Token Request Error: ",r.status_code)
            print("Error in creating playlist")
            print(r.json())
            return {}
        elif r.status_code == 200:
            print("Playlist Created.")
            r_new = r.json()
            new_playlist = r_new['id']
            return new_playlist
        else:
            print("Playlist Created.")
            r_new = r.json()
            new_playlist = r_new['id'] 
            return new_playlist #Returns the playlist's Spotify ID

    #Helper function that fetches playlist features, performs playlist scrape
    def playlist_parser(self,pl_list,pl_name_req):
        while pl_list['next']!=None:
            curr_page = pl_list['items']
            for index in range(len(curr_page)):
                pl_name = curr_page[index].get('name')
                if pl_name == pl_name_req:
                    print('Performing Playlist Scrape of: ',pl_name)
                    pl_id = curr_page[index].get('id')
                    target_pl,tpl_obj = self.playlist_scrape(pl_id) #Target playlist for random reshuffling, includes audiofeat extraction
                    return target_pl
            next_ep = pl_list['next']
            r = requests.get(next_ep,headers=self.get_access_header())
            pl_list = self.process_request(r)
        curr_page = pl_list['items']
        for index in range(len(curr_page)):
            pl_name = curr_page[index].get('name')
            if pl_name == pl_name_req:
                print('Performing Playlist Scrape of: ',pl_name)
                pl_id = curr_page[index].get('id')
                target_pl,tpl_obj = self.playlist_scrape(pl_id) #Target playlist for random reshuffling, includes audiofeat extraction
                return target_pl

    #Function that retrieve's a list of the tracks given a playlist id, performs song id extraction followed by MIR
    def playlist_scrape(self,playlistid):
        playlist =  self.get_playlist_tracks(playlistid)    #Retrieves Spotify Playlist Object given Spotify ID
        track_ids = self.get_song_ids(playlist,0) #Returns specific json string for audio feature API request
        track_features = self.extract_audio_analysis(track_ids)  #Returns audio features of a given playlist
        print('Playlist scrape complete.')
        return track_features, playlist

    #Function that adds a list of songs (Spotify ID's) to a given playlist 
    def playlist_add(self,playlist_id,spotify_uri):
        headers = self.get_access_header()
        cap = len(spotify_uri)
        endpoint = "https://api.spotify.com/v1/playlists//tracks"
        endpoint = endpoint[:37] + playlist_id + endpoint[37:]
        if len(spotify_uri)> 100:
            while cap >0:
                query_params = {'uris':spotify_uri[:100]}
                r = requests.post(endpoint,json=query_params,headers=headers)
                print('Adding Tracks To Playlist...')
                res = self.process_request(r)
                spotify_uri = spotify_uri[100:]
                cap-=100
        else:
            query_params = {'uris':spotify_uri}
            r = requests.post(endpoint,json=query_params,headers=headers)
            print('Adding Tracks To Playlist...')
            res = self.process_request(r)
        return res


#Audio Analysis Functions:
    #Function that returns an object of audio features for a given list of tracks
    def extract_audio_analysis(self,ids):
        endpoint = 'https://api.spotify.com/v1/audio-features'
        headers = self.get_access_header()
        id_len  = len(ids)
        id_count = id_len
        ids_audio = ids
        track_list = []         
        print('Requesting audio features of tracks...')
        if id_len > 100:
            while id_count > 0: #Going over Spotify's limit of over 100 entries
                id_string = ','.join(ids_audio[:100])
                query_params = {'ids':id_string}
                #Requesting audio-features of given Spotify ID's
                r = requests.get(endpoint,headers=headers,params=query_params)
                tracks_features = self.process_request(r)
                track_list.append(tracks_features)
                ids_audio = ids_audio[100:]
                id_count -=100
        else:
            id_string = ','.join(ids_audio)
            query_params = {'ids':id_string}
            #Requesting audio-features of given Spotify ID's
            r = requests.get(endpoint,headers=headers,params=query_params)
            tracks_features = self.process_request(r)
            track_list.append(tracks_features)
        #Fetching Spotify track id's
        endpoint = 'https://api.spotify.com/v1/tracks' #Using Tracks Endpoint, with ids as query parameters for Spotify IDS
        track_features_list = []
        print('Extracting audio features...')
        if id_len > 50: #Going over the 50 limit of parsing audio features
            id_count = len(ids)
            while id_count > 0:
                print('Processing...')
                #Request track objects for a list of 50 specified track ids, at a time
                id_string = ''
                id_string = ','.join(ids[:50])
                query_params = {'ids':id_string}
                r = requests.get(endpoint,headers=headers,params=query_params)
                tracks_dict = self.process_request(r)
                for track in tracks_dict['tracks']:
                    endpoint_sec = 'https://api.spotify.com/v1/audio-analysis/'+track['id']
                    for page in track_list:
                        song_features,index = self.parse_audio_features(page,track['id'])
                        if song_features is not None:
                            artist = track['artists']
                            artist = artist[0]
                            if 'genres' in artist:
                                genres = artist['genres']
                                r_2 = requests.get(endpoint_sec,headers=headers)
                                r_2 = self.process_request(r_2)
                                subpage = page['audio_features']
                                subpage = subpage[index]
                                song_features.update({'Title': track['name'],'Artist': artist['name'],'Genre': genres[0],'Audio Analysis': r_2,'Key': page['key']})
                                track_features_list.append(song_features)
                            else:
                                r_2 = requests.get(endpoint_sec,headers=headers)
                                r_2 = self.process_request(r_2)
                                subpage = page['audio_features']
                                subpage = subpage[index]
                                song_features.update({'Title': track['name'],'Artist': artist['name'],'Genre': 'N/A','Audio Analysis': r_2,'Key': subpage['key']})
                                track_features_list.append(song_features)
                ids = ids[50:]
                id_count -=50
        else:
            id_string = ''
            id_string = ','.join(ids)
            query_params = {'ids':id_string}
            r = requests.get(endpoint,headers=headers,params=query_params)
            tracks_dict = self.process_request(r)
            for track in tracks_dict['tracks']:
                endpoint_sec = 'https://api.spotify.com/v1/audio-analysis/'+track['id']
                song_features,index = self.parse_audio_features(tracks_features,track['id'])
                for page in track_list:
                    if song_features is not None:
                        artist = track['artists']
                        artist = artist[0]
                        if 'genres' in artist:
                            genres = artist['genres']
                            r_2 = requests.get(endpoint_sec,headers=headers)
                            r_2 = self.process_request(r_2)
                            subpage = page['audio_features']
                            subpage = subpage[index]
                            song_features.update({'Title': track['name'],'Artist': artist['name'],'Genre': genres[0],'Audio Analysis': r_2,'Key': page['key']})
                            track_features_list.append(song_features)
                        else:
                            r_2 = requests.get(endpoint_sec,headers=headers)
                            r_2 = self.process_request(r_2)
                            subpage = page['audio_features']
                            subpage = subpage[index]
                            song_features.update({'Title': track['name'],'Artist': artist['name'],'Genre': 'N/A','Audio Analysis': r_2,'Key': subpage['key']})
                            track_features_list.append(song_features)
        return track_features_list

    #Function that parses through audio features from returned spotify object, via song id
    def parse_audio_features(self,playlist,song_id):
        index = 0
        for song in playlist['audio_features']:
            if song != None and song['id'] == song_id:
                song_features = song.copy()
                song_features.pop('type')
                song_features.pop('liveness')
                song_features.pop('speechiness')
                song_features.pop('track_href')
                song_features.pop('analysis_url')
                song_features.pop('duration_ms')
                song_features.pop('time_signature')
                return song_features,index
            index = index+1
        song_features = None
        return song_features,index

    #Function that returns feature vector discluding Spotify URI info for given song
    def feature_vector_extraction(self,song):
        feature_vector = [
            song['danceability'],
            song['acousticness'],
            song['energy'],
            song['instrumentalness'],
            song['valence'],
            song['key']
            ]
        return feature_vector

    #Function that returns vector containing Spotify URI info for given song object
    def feature_id(self,song):
        id_vector = [
            song['id'],
            song['uri']]
        return id_vector

    def create_pl_vector(self,playlist):
            print('Initializing and formatting playlist vector...')
            idset = [] #ID set for Spotify ID Vectors
            featset = [] #Feature set for Spotify song
            plslist = [] #Playlist Session List, containig both features vector and URI vector
            titleset = []
            audanset = [] #List for Spotify Audio Analysis Objects
            artistset = [] #List of Artists within playlist
            genreset = [] #List of genres of all the playlist tracks, in sequential order
            keyset = [] #List of keys for all playlist tracks, in sequential order
            temposet = []
            #Creating Spotify ID vectors for given playlist
            i = 0
            pl_len = len(playlist)
            while i < pl_len:
                if i < len(playlist):
                    track = playlist[i]
                    aa = track.get('Audio Analysis')
                    check = aa.get('track')
                    if check:
                        idset.append(self.feature_id(track)) 
                        featset.append(self.feature_vector_extraction(track))
                        titleset.append(track.get('Title'))
                        audanset.append(aa.get('track'))
                        artistset.append(track.get('Artist'))
                        genreset.append(track.get('Genre'))
                        keyset.append(track.get('Key'))
                        aud_ana = track.get('Audio Analysis')
                        track_info = aud_ana.get('track')
                        temposet.append(track_info['tempo'])
                        i+=1
                    else:
                        playlist.pop(i)
                else:
                    i+=1
            for index in range(len(playlist)):
                plslist.extend([{"Features": featset[index],"URIs": idset[index],'Title': titleset[index],'Artist': artistset[index],'Audio Analysis': audanset[index],'Genre': genreset[index],'Key': keyset[index],'Tempo': temposet[index]}])
            print('Complete')
            return plslist