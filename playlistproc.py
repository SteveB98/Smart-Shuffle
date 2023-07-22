import random
import numpy as np
from operator import itemgetter
#Program: playlistproc.py
#Author: Steve Berg
#Last Updated: July 16, 2023
#Date Created: Jan 5, 2021
#Purpose: Hosts several helper function utilized in the init file for graphing, datapoint comparisons, and formatting vectors for song sequencing

#Utilizes Authorization Code Flow with PKCE
#Add a vertex to the dictionary
def add_vertex(title,v,graph):
    if title not in graph:
        tempo = v.get('Tempo')
        graph[title] = [str(tempo)]
    return graph

def swap(a,b,l):
    newlist = l[:]
    newlist[a],newlist[b] = newlist[b],newlist[a]
    return newlist
# Add an directed edge from vertex v1 to v2 with edge weight e, given some graph
def add_edge(v1, v2, e,graph):
    #Check if vertex v1 is a valid vertex
    if v1 in graph and v2 in graph:
        temp = [v2, e]
        graph[v1].append(temp)
    return graph

def tempo_check(node,bounds):
    mintb = bounds[0]
    medtb = bounds[1]
    if int(float(node[0]))< mintb: return 'Low'
    elif int(float(node[0])) < medtb and int(float(node[0]))>mintb: return 'Med'
    else: return 'High'

def tempo_path(shuffle_path,uspl_vector,b):
    #Additional function to visualize the sequence as tempo states
    min_tempo_bound = b[0]
    med_tempo_bound = b[1]
    tempo_path = []
    #Taking each title from returned reordering
    for title in shuffle_path:
        #Compares to original ordering
        for vec in uspl_vector:
            for song in vec[0]:
                if song.get('Title') in title:
                    if song.get('Tempo') < min_tempo_bound: tempo_path.append('Low')
                    elif song.get('Tempo') < med_tempo_bound and song.get('Tempo')>min_tempo_bound: tempo_path.append('Med')
                    else: tempo_path.append('High')
                    break
    print(tempo_path)

def add_key(title,v,graph):
    if title in graph:
        key = v.get('Key')
        if key not in graph[title]: graph[title].extend([key])
    return graph

#Returns list of neighboring vectors given target vertex and graph
def get_neighbors(v,graph):
    neighbors = []
    for edges in graph[v]:  neighbors.append(edges)
    return neighbors[1:-1]

def print_graph(graph):
    for vertex in graph:
        for edges in graph[vertex]:
            if type(edges)== int: break
            print(vertex, " -> ", edges[0], " edge weight: ", edges[1])

#Helper funtion that vertifies if a song2 is within song1's key, or, song2 is diatonic to song1. If so, return Euclidean distance between the two key centers, -1 otherwise
#Two cases are done doing chromatic distances, split into two arrays
def inkey(init_song,target_song):
    key_names_dict = {0:'C',1:'C#/Db',2:'D',3:'D#/Eb',4:'E',5:'F',6:'F#/Gb',7:'G',8:'G#/Ab',9:'A',10:'A#/Bb',11:'B'}
    key = key_names_dict.get(init_song)
    if key == 'C':
        target_key = key_names_dict.get(target_song)
        key_notes = ['C','D','Eb','E','F']
        key_notes_2 = ['C','B','Bb','A','G']
        if target_key in key_notes:  return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key))   
    if key == 'C#/Db':
        target_key = key_names_dict.get(target_song)
        key_notes = ['C#/Db','D#/Eb','E','F','F#/Gb']
        key_notes_2 = ['C#/Db','C','B','A#/Bb','G#/Ab']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key))   
    if key == 'D':
        target_key = key_names_dict.get(target_song)
        key_notes = ['D','E','F','F#/Gb','G']
        key_notes_2 = ['D','C#/Db','C','B','A']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key))   
    if key == 'D#/Eb':
        target_key = key_names_dict.get(target_song)
        key_notes = ['D#/Eb','F','F#/Gb','G','G#/Ab']
        key_notes_2 = ['D#/Eb','D','A#/Bb','C#/Db','C']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'E':
        target_key = key_names_dict.get(target_song)
        key_notes = ['E','F#/Gb','G','G#/Ab','A']
        key_notes_2 = ['E','D#/Eb','D','C#/Db','B']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'F':
        target_key = key_names_dict.get(target_song)
        key_notes = ['F','G','G#/Ab','A','A#/Bb']
        key_notes_2 = ['F','E','D#/Eb','D','C']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'F#/Gb':
        target_key = key_names_dict.get(target_song)
        key_notes = ['F#/Gb','G#/Ab','A','A#/Bb','B']
        key_notes_2 = ['F#/Gb','F','E','D#/Eb','C#/Db']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'G':
        target_key = key_names_dict.get(target_song)
        key_notes = ['G','A','A#/Bb','B','C']
        key_notes_2 = ['G','F#/Gb','F','E','D']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'G#/Ab':
        target_key = key_names_dict.get(target_song)
        key_notes = ['G#/Ab','A#/Bb','B','C','C#/Db']
        key_notes_2 = ['G#/Ab','G','F#/Gb','F','D#/Eb']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'A':
        target_key = key_names_dict.get(target_song)
        key_notes = ['A','B','C','C#/Db','D']
        key_notes_2 = ['A','G#/Ab','G','F#/Gb','E']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'A#/Bb':
        target_key = key_names_dict.get(target_song)
        key_notes = ['A#/Bb','C','C#/Db','D','D#/Eb']
        key_notes_2 = ['A#/Bb','A','G#/Ab','G','F']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    if key == 'B':
        target_key = key_names_dict.get(target_song)
        key_notes = ['B','C#/Db','D','D#/Eb','E']
        key_notes_2 = ['B','A#/Bb','A','G#/Ab','F#/Gb']
        if target_key in key_notes: return np.linalg.norm(key_notes.index(key)-key_notes.index(target_key))
        if target_key in key_notes_2:  return np.linalg.norm(key_notes_2.index(key)-key_notes_2.index(target_key)) 
    return -1

def tempo_dist(init_node,target_node,bounds):
    mintb = bounds[0]
    medtb = bounds[1]
    maxtb = bounds[2]
    mintempo = bounds[3]
    in_tempo = tempo_check(init_node,bounds)
    tn_tempo = tempo_check(target_node,bounds)
    dist = 0
    if in_tempo == 'Med' and tn_tempo == "High":
        tempo_denominator = maxtb-(medtb+1)
        dist = np.linalg.norm(int(float(init_node[0]))-int(float(target_node[0])))/tempo_denominator
    if in_tempo == 'Med' and tn_tempo == "Low":
        tempo_denominator = mintb-mintempo
        dist = np.linalg.norm(int(float(init_node[0]))-int(float(target_node[0])))/tempo_denominator
    return dist

def shuffle_traversal(g,b,f):
    graph_list = list(g.items())
    init_vertex = graph_list[0]
    frontier = []
    shuffle_path = []
    frontier.append(init_vertex)
    curr_tempo = tempo_check(init_vertex[1],b) #Setting before processing to account for starting on the initial vertex
    prev_tempo = curr_tempo #Handles edge case of inital start, comparing to self for edge weight assignation
    tempo_ref = {'Low': 1,'Med': 2, 'High':3}
    while frontier:
        node = frontier.pop()
        curr_tempo = tempo_check(node[1],b)
        shuffle_path.append(node[0])
        neighbors = get_neighbors(node[0],g)
        for next_node in neighbors:
            #Extracting Vertex object from graph to get tempo
            if type(next_node) is not int:
                nn_v = [item for item in graph_list if next_node[0] in item]
                next_tempo = tempo_check(nn_v[0][1],b)    #Retrieving tempo of neighbor
                if tempo_ref[curr_tempo]+tempo_ref[next_tempo]==5 and tempo_ref[prev_tempo]==1: next_node[1]+=1.0*tempo_dist(node[1],nn_v[0][1],b)
                if (tempo_ref[curr_tempo]+tempo_ref[next_tempo])==3 and tempo_ref[prev_tempo] ==3: next_node[1]+=1.0*tempo_dist(node[1],nn_v[0][1],b)
                key_mult = inkey(node[-1][-1],nn_v[0][-1][-1])
                #For key centers, a penalty is applied if neighbor is not diatonic. If so, penalty is modified based on intervalic diatonic distance between the two keys
                if key_mult!=-1 : next_node[1]+=1.0*(key_mult/5)
                else: next_node[1]+= 1.0
        neighbors = sorted(neighbors,key=itemgetter(1),reverse=True) #Sorting neighbors by edge weight, for sorted frontier path
        for next_node in reversed(neighbors):
            if next_node[0] not in shuffle_path and type(next_node[0]) is not int: #Add vertex to frontier path, if not visited yet (already in sorted path done priorly)
                #Extracting Vertex object from graph, to append to frontier and reached lists
                next_node = [item for item in graph_list if next_node[0] in item]
                frontier.append(next_node[0])
                break
        prev_tempo = tempo_check(node[1],b)
    return shuffle_path