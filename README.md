# Smart Shuffle (Web Application using Python and Flask)

## A functional Python-based software application that generates randomized Spotify playlist shuffles using its content's song attributes and a given user playlist

### :toolbox: Languages and Tools
<img align="left" alt="Python" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg">
<img align="left" alt="Flask" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/flask/flask-original.svg">
<img align="left" alt="Anaconda" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/adonisjs/adonisjs-original.svg">
<img align="left" alt="Pandas" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pandas/pandas-original.svg">
<img align="left" alt="NumPY" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/numpy/numpy-original.svg">
<img align="left" alt="VSCode" width="30px" style="padding-right:10px;" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vscode/vscode-original.svg">
<p>&nbsp;</p>

This project was done for an academic project in coordination with a computer science faculty member. Given a Spotify account, the application selects a user playlist as desired and generates a tracklist sequence based on its metadata from each individual song. The full program executes the following:

* Creates frontend web pages for user sign-in and playlist selection
* Backend executes authorized sign-in and metadata retrieval by communicating with Spotify API
* Organizes fetched metadata and performs list processing given certain parameters
* Saves the new shuffled playlist into the user library without modification of the source playlist
* Can graph specific playlist attributes over the course of the tracklist as a visual aid (IMPLEMENTATION INFORMATION COMING SOON)

---
## Installation Instructions
1. Clone this project
2. Setup a local directory for executable creation
3. Setup a programming environment via Anaconda or a similar bash shell with the repository's .YML file
4. You must set up a Spotify Developer account with your own user ID and secret key, which must be updated in __init__.py
5. Run smartshufflesetup.py on localhost or set it up on a alternative hosting platform i.e. PythonAnywhere
