from ast import Continue
import os
from re import I
import pkce
import numpy as np
import time
import random
import requests
import statistics as stats
from openpyxl import Workbook
from scipy.stats import spearmanr
from gevent.pywsgi import WSGIServer
from flask import Flask
from flask import (Blueprint, Flask, flash, g, redirect, render_template,request, session, url_for)
from .spotifyAPI import SpotifyAPI
from .playlistproc import add_edge, add_key, add_vertex, print_graph, shuffle_traversal, tempo_path, swap
import chromedriver_binary
from selenium.webdriver import Chrome
from .smartshufflegraphing import graphing_routines, pl_audio_analysis_bokeh,pl_audio_features_bokeh,song_audio_features_bokeh
#Program: Smart Shuffle
#Author: Steve Berg
#Last Updated: July 21, 2023
#Date Created: Jan 5, 2021
#Purpose: A web-based app that processes and reorders a given Spotify Playlist, determined by feature analysis from Spotify's web API
#Insert dev ID/PW if running application on localhost
#Graphing routines aren't neccessary for core functionality, can be enabled if desired to see visual breakdown of playlists & attributes

#Flask App Functions:
def create_app(test_config=None):
    # create and configure the app, creating Code Vertifier and Challenge Code for auth
    app = Flask(__name__, instance_relative_config=True,static_url_path='/static')
    user_id =  dev_id
    spotify_session = SpotifyAPI(user_id,dev_secret_key)
    code_verifier = pkce.generate_code_verifier(length=128)
    code_challenge = pkce.get_code_challenge(code_verifier)
    app.config.from_mapping(
        SECRET_KEY='dev',
         #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'), Implement if using database system
          )
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

    #Redirect to helloworld page, to get targeted playlist
    @app.route('/')
    def home():
        return redirect(url_for('smartshuffle'))

    #Fetch client playlist to reshuffle, redirect to process
    @app.route('/smartshuffle', methods=['GET','POST'])
    def smartshuffle():
        return render_template('musicrec.html')

    #Using entered values via web-end HTML form entry
    @app.route('/process', methods = ['GET','POST'])
    def process():
        playlist = request.args.get('playlist')
        newname = request.args.get('playlistname')
        spotify_session.playlist = playlist
        spotify_session.newname = newname
        res_url = spotify_session.get_auth_uri(user_id,code_challenge)   #Creates target URL for code and state variables after access_token request
        spotify_session.perform_auth()
        return redirect(res_url)

    #Webpage for processing, initiate reshuffle
    @app.route('/smartplaylist')
    def smartplaylist():
        code = request.args.get('code') #Vertifier code for fetching user access token
        state = request.args.get('state') #State vertifier, to confirm transaction intergrity has not been compromised
        if state==spotify_session.auth_state:
            spotify_session.test_flag = True #See if test_flag is neccessary at this point
            spotify_session.get_user_access_token(user_id,code_verifier,code) #Fetching user access token for Spotify API requests
            #Going into each playlist Spotify object, parse through and perform a name check to fetch the corresponding playlist to given name (web-side)
            playlist_name = spotify_session.playlist
            pl_list = spotify_session.get_client_playlists() #Compiles and fetches a list of user's playlists
            pl = spotify_session.playlist_parser(pl_list,playlist_name)
            #Extracting songs from playlist
            uspl_vector = []
            tempo = []
            song_occur = {}  #Helper Dict to keep track of song occurances, handling duplicate vertices upon naming
            playlist_path = []
            if pl is not None:
                uspl_vector.append([spotify_session.create_pl_vector(pl),playlist_name])
                #Graphing of Regularly & Shuffled Sequenced Playlists
                #graphing_routines(uspl_vector[0])
                for playlist_vec in uspl_vector:
                    for song in playlist_vec[0]:
                        title = song.get('Title') + '_' + song.get('Artist')+'_1'
                        #feats = song.get('Features')
                        tempo.append(song.get('Tempo'))
                        if song.get('Title') not in song_occur: song_occur[song.get('Title')] = 1 #If song hasn't been processed, add an occurance
                        else: 
                            song_occur[song.get('Title')] += 1
                            title = song.get('Title') + '_' + song.get('Artist')+'_'+str(song_occur[song.get('Title')])
                        playlist_path.append(title)
                        song['Title'] = title
                    if playlist_vec == uspl_vector[0]: playlist_vec[0] = sorted((i for i in playlist_vec[0]),key=lambda x: (x.get('Tempo')))
            #graphing_routines(uspl_vector[0])
            min_tempo = min(tempo)
            max_tempo = max(tempo)
            min_tempo_bound = min_tempo+((max_tempo-min_tempo)/3)
            med_tempo_bound = min_tempo_bound+((max_tempo-min_tempo)/3)
            g = {}
            for playlist_vec in uspl_vector:
                index = 0
                for song1 in playlist_vec[0]:
                    s1_title = song1.get('Title')
                    s1f = song1['Features']
                    s1f = np.array(s1f[:-1])
                    s1f = np.linalg.norm(s1f)
                    g = add_vertex(s1_title,song1,g)
                    for song2 in playlist_vec[0]:
                        s2_title = song2.get('Title')
                        s2f = song2['Features']
                        s2f = np.array(s2f[:-1])
                        s2f = np.linalg.norm(s2f)
                        comp_tempo = song2.get('Tempo')
                        g = add_vertex(s2_title,song2,g)
                        dist = np.linalg.norm(s1f-s2f)
                        if s1_title!=s2_title:
                            #Both songs are low tempo
                            if tempo[index] < min_tempo_bound and comp_tempo < min_tempo_bound: g = add_edge(s1_title,s2_title,1.0+dist,g)
                            #Song 1 is low tempo and song 2 is med tempo
                            if tempo[index] < min_tempo_bound and (comp_tempo > min_tempo_bound and comp_tempo < med_tempo_bound): g = add_edge(s1_title,s2_title,0.5+dist,g)
                            #Song 1 is low tempo and song 2 is high tempo
                            if tempo[index] < min_tempo_bound and comp_tempo > med_tempo_bound: g = add_edge(s1_title,s2_title,1.0+dist,g)
                            #Song 1 is med tempo and song 2 is low Tempo
                            if (tempo[index]>min_tempo_bound and tempo[index] < med_tempo_bound) and comp_tempo < min_tempo_bound:g = add_edge(s1_title,s2_title,0.5+dist,g)
                            #Both Songs are med tempo
                            if (tempo[index]>min_tempo_bound and tempo[index] < med_tempo_bound) and (comp_tempo > min_tempo_bound and comp_tempo < med_tempo_bound): g = add_edge(s1_title,s2_title,1.0+dist,g)
                            #Song 1 is med tempo and song 2 is high tempo
                            if (tempo[index]>min_tempo_bound and tempo[index] < med_tempo_bound) and comp_tempo > med_tempo_bound: g = add_edge(s1_title,s2_title,0.5+dist,g)
                            #Both Songs are high tempo
                            if tempo[index]>med_tempo_bound and comp_tempo > med_tempo_bound: g = add_edge(s1_title,s2_title,1.0+dist,g)
                            #Song 1 is high tempo and song 2 is med tempo
                            if tempo[index]>med_tempo_bound and (comp_tempo < med_tempo_bound and comp_tempo > min_tempo_bound): g = add_edge(s1_title,s2_title,0.5+dist,g)
                            #Song 1 is high tempo and song 2 is low tempo
                            if tempo[index]>med_tempo_bound and comp_tempo < min_tempo_bound: g = add_edge(s1_title,s2_title,1.0+dist,g)
                    g = add_key(s1_title,song1,g) #As last element of vertex obj
                    index+=1
                shuffle_path = shuffle_traversal(g,(min_tempo_bound,med_tempo_bound,max_tempo,min_tempo),f=lambda n: -len(n))
                #tempo_path(shuffle_path,uspl_vector,(min_tempo_bound,med_tempo_bound))
                #print(shuffle_path,len(shuffle_path))
                uri_list = []
                shffld_seq = []
                for track in shuffle_path:
                    track = track.split('_',1)
                    track_obj = [item for item in uspl_vector[0][0] if track[0] in item["Title"]]
                    shffld_seq.extend(track_obj)
                    uris = track_obj[0].get('URIs')
                    uri_list.append(uris[1])
                #uspl_shffld = [shffld_seq,playlist_name+' Shuffled']
                #graphing_routines(uspl_shffld)
                spotify_session.playlist_add(spotify_session.create_playlist(spotify_session.newname),uri_list)#Adds a list of spotify tracks to a given playlist, with required Spotify Id's respectively
                pl_list = spotify_session.get_client_playlists() #Compiles and fetches a list of user's playlists
                curr_page = pl_list['items']
                while pl_list['next'] != None:
                    for playlist in curr_page:
                        if playlist['name']==spotify_session.newname:
                            uri = playlist['uri']
                            uri = uri[17:]
                            embed = "https://open.spotify.com/embed/playlist/"+uri+'?utm_source=generator'
                    next_page = pl_list['next']
                    r = requests.get(next_page,headers=spotify_session.get_access_header())
                    pl_list = spotify_session.process_request(r)
                for playlist in curr_page:
                    if playlist['name']==spotify_session.newname:
                        uri = playlist['uri']
                        uri = uri[17:]
                        embed = "https://open.spotify.com/embed/playlist/"+uri+'?utm_source=generator'
            return render_template('musicrecdone.html',var1 = embed)
        else:
            print('Error in state vertification, going back to home screen...')
            return render_template('musicrec.html')
    with app.test_request_context():
        print(url_for('smartshuffle'))
    #if __name__ == '__main__':
        #app.run(host="127.0.0.1", port=5000, debug=True)
    return app
