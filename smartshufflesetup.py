import os
#Python program that executes shell commands for activating Smart Shuffle Application


os.environ['FLASK_APP']= 'flaskr'
os.environ['FLASK_ENV'] ='development'
os.system('flask run --host=127.0.0.1')