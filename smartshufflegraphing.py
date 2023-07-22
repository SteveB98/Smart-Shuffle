from bokeh.io import export_png
from bokeh.plotting import figure, show
from bokeh.models import LabelSet, ColumnDataSource
from bokeh.transform import cumsum
from bokeh.palettes import Category20c
from bokeh.layouts import row
from scipy.signal import medfilt
from math import pi
from statistics import mean, stdev
import os
from selenium import webdriver
import chromedriver_binary
import pandas as pd
import matplotlib.pyplot as plt
#Program: smartshufflegraphing.py
#Author: Steve Berg
#Last Updated: Feb 16, 2022
#Date Created: Feb 16, 2022
#Purpose: A bokeh graphing extension for the Smart Shuffle APplication, for research purposes
#Class API for Spotify Web interaction

def pl_audio_analysis_bokeh(playlist):
    key_names_dict = {0:'C',1:'C#/Db',2:'D',3:'D#/Eb',4:'E',5:'F',6:'F#/Gb',7:'G',8:'G#/Ab',9:'A',10:'A#/Bb',11:'B'}
    key_count_dict = {'C':0,'C#/Db':0,'D':0,'D#/Eb':0,'E':0,'F':0,'F#/Gb':0,'G':0,'G#/Ab':0,'A':0,'A#/Bb':0,'B':0}
    key_names_axis = ['C','C#/Db','D','D#/Eb','E','F','F#/Gb','G','G#/Ab','A','A#/Bb','B']
    x = range(len(playlist[0]))
    tempo = []
    loudness = []
    key_path = []
    for song in playlist[0]:
        aud_ana = song.get('Audio Analysis')
        #track_info = aud_ana.get('track')
        tempo.append(song.get('Tempo'))
        loudness.append(aud_ana['loudness'])
        key_path.append(key_names_dict.get(song['Key']))
        key_count_dict[key_names_dict.get(song['Key'])] = key_count_dict.get(key_names_dict.get(song['Key'])) + 1
    title = playlist[1]
    print(title)
    #Configuring Audio Analysis, Key Path, and Key Count Graphs
    p = figure(title='Audio Analysis of: '+title,x_axis_label='Playlist Tracks',y_axis_label='Tempo(BPM)/Loudness(dB)')
    p.line(x=x,y=tempo,legend_label='Tempo',color='blue',line_width=2)
    p.line(x=x,y=loudness,legend_label='Loudness',color='red',line_width=2)
    p.legend.location="top_left"
    p.legend.title="Components"
    kc = figure(title=title+" Key Map Statistics",x_range = key_names_axis)
    kc.vbar(x=key_names_axis,top=list(key_count_dict.values()),width=0.8)
    kp = figure(title=playlist[1]+" Key Map Path",x_axis_label='Playlist Tracks',y_range = key_names_axis,y_axis_label='Keys')
    kp.step(x=x,y=key_path,legend_label='Keys',color='green',mode='center',line_width=4)
    kp.legend.location="top_left"

    #Key Count in Pie Chart Graph
    data = pd.Series(key_count_dict).reset_index(name='value').rename(columns={'index': 'key'})
    data['angle'] = data['value']/data['value'].sum() * 2*pi
    data['color'] = Category20c[len(key_count_dict)]
    kpc = figure(height=350, title=title+" Key Map Statistics", toolbar_location=None,
        tools="hover", tooltips="@key: @value", x_range=(-0.5, 1.0))
    kpc.wedge(x=0, y=1, radius=0.4,
    start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
    line_color="white", fill_color='color', legend_field='key', source=data)
    data["value"] = data['value'].astype(str)
    data["value"] = data["value"].str.pad(35, side = "left")   
    source = ColumnDataSource(data)
    labels = LabelSet(x=0, y=1, text='value',
    angle=cumsum('angle', include_zero=True), source=source, render_mode='canvas')
    kpc.add_layout(labels)
    kpc.axis.axis_label = None
    kpc.axis.visible = False
    kpc.grid.grid_line_color = None
    return p,kc,kp,kpc

def pl_audio_features_bokeh(playlist):
    x = range(len(playlist[0]))
    d_y=[] #dancibility of features
    a_y=[] #acousticness of features
    e_y=[] #energy of features
    i_y=[] #instrumentalness of features
    v_y=[] #valence of features
    #Extracting Features for graphing
    for song in playlist[0]:
        y = song['Features']
        d_y.append(y[0])
        a_y.append(y[1])
        e_y.append(y[2])
        i_y.append(y[3])
        v_y.append(y[4])
    #Creating and showing Bokeh graph
    p = figure(title='Song Features of: '+playlist[1],x_axis_label='Playlist Tracks',y_axis_label='Feature Intensity')
    p.line(x=x,y=d_y,legend_label='Danceability',color='blue',line_width=2)
    p.line(x=x,y=e_y,legend_label='Energy',color='green',line_width=2)
    p.line(x=x,y=v_y,legend_label='Valence',color='red',line_width=2)
    p.legend.location="top_left"
    p.legend.title="Song Features"

    p1 = figure(title='Song Features of: '+playlist[1],x_axis_label='Playlist Tracks',y_axis_label='Feature Intensity')
    p1.line(x=x,y=d_y,legend_label='Danceability',color='blue',line_width=2)
    p1.line(x=x,y=e_y,legend_label='Energy',color='green',line_width=2)
    p1.legend.location="top_left"
    p1.legend.title="Song Features"

    p2 = figure(title='Song Features of: '+playlist[1],x_axis_label='Playlist Tracks',y_axis_label='Feature Intensity')
    p2.line(x=x,y=d_y,legend_label='Energy',color='blue',line_width=2)
    p2.line(x=x,y=v_y,legend_label='Valence',color='red',line_width=2)
    p2.legend.location="top_left"
    p2.legend.title="Song Features"

    #Additional Statistical Calculations
    dy_m = mean(d_y)
    ay_m = mean(a_y)
    ey_m = mean(e_y)
    iy_m = mean(i_y)
    vy_m = mean(v_y)
    dy_std = stdev(d_y)
    ay_std = stdev(a_y)
    ey_std = stdev(e_y)
    iy_std = stdev(i_y)
    vy_std = stdev(v_y)
    means = [dy_m,ay_m,ey_m,iy_m,vy_m]
    stds = [dy_std,ay_std,ey_std,iy_std,vy_std]
    return p,p1,p2,means,stds

def smooth_features(x, sr, hop_length, filter_length=21, downsample_hz=2):
    #Apply temporal smoothing to a frame-by-frame feature array
    # Apply median smoothing
    smoothed = medfilt(x, kernel_size=(1,filter_length))
    # Downsample the smoothed signal
    downsample_rate = int((sr / hop_length) / downsample_hz)
    smoothed = smoothed[:, ::downsample_rate]
    # The update length in samples between features
    step_size = downsample_rate * hop_length
    return smoothed, step_size 

def song_audio_features_bokeh(playlist,limit):
    i = 0
    d_y=[] #dancibility of features
    a_y=[] #acousticness of features
    e_y=[] #energy of features
    i_y=[] #instrumentalness of features
    v_y=[] #valence of features
    #Extracting Features for graphing
    for song in playlist[0]:
        pl_title = song['Title']
        artist = song['Artist']
        genre = song['Genre']
        y = song['Features']
        d_y = y[0]
        a_y = y[1]
        e_y = y[2]
        i_y = y[3]
        v_y = y[4]
        tops = [d_y,a_y,e_y,i_y,v_y]
        #Creating and showing Bokeh graph
        feats = ['Danceability','Acousticness','Energy','Instrumentalness','Valance']
        if genre is None and artist is not None:   p = figure(title="Song Features for "+pl_title+' by '+artist+': No Genre Assigned ',x_range=feats,y_axis_label='Feature Intensity')
        elif genre is None and artist is None: p = figure(title="Song Features for "+pl_title+': No Genre Assigned ',x_range=feats,y_axis_label='Feature Intensity')
        elif artist is None and genre is not None: p = figure(title="Song Features for "+pl_title+': '+genre,x_range=feats,y_axis_label='Feature Intensity')
        else:   p = figure(title="Song Features for "+pl_title+' by '+artist+': '+genre,x_range = feats,y_axis_label='Feature Intensity')
        p.vbar(x=feats,top=tops,width=0.8)
        export_png(p, filename=pl_title+" Audio Features.png")
        i = i+1
        if i >= limit: break

def graphing_routines(vector):
    for index in range(len(vector)-1):
            name=vector[1]
            path = 'C:/Users/steph/Documents/AllProgramming/CSC497Proj/Graphing/Subset Random Song/'+name+'/'
            if os.path.exists(path)==0: os.mkdir(path)
            g1,g2,g3,g4 = pl_audio_analysis_bokeh(vector) #Retruns Tempo/Loudness, Key Path and Statistics Line and Pie Graphs
            g5,g6,g7,means,stds = pl_audio_features_bokeh(vector) #Returns a series of feature graphs: Summed Together, Dancibility and Energy, and Dancibility and Valance
            row1 = row(g1,g3)
            row2 = row(g2,g4)
            row3 = row(g5)
            row4 = row(g6,g7)
            driver = webdriver.Chrome('C:/Users/steph/miniconda3/envs/SmartShuffle/Lib/site-packages/chromedriver_binary/chromedriver.exe') 
            export_png(row1,filename=path+name+' Audio Feature Graphing.png')
            export_png(row2,filename=path+name+' Audio Feature Graphing - Key Map and Statistics.png')
            export_png(row3,filename=path+name+' Metadata Graphing.png')
            export_png(row4,filename=path+name+' Metadata Graphing - Separate Features.png')