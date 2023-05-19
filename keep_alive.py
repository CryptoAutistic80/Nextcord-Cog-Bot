from flask import Flask  # Importing the Flask class from the flask module
from threading import Thread  # Importing the Thread class from the threading module

app = Flask('')  # Creating a Flask application

@app.route('/')  # Decorator to define the route for the home page
def home():
    return "I'm Alive"  # Returns a simple message indicating that the server is alive

def run():
    app.run(host='0.0.0.0', port=8080)  # Starts the Flask application on host '0.0.0.0' and port 8080

def keep_alive():
    t = Thread(target=run)  # Creates a new Thread that will run the Flask application
    t.start()  # Starts the Thread
