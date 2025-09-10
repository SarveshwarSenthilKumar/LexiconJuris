
from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
from flask_session import Session
from datetime import datetime
import pytz
import os
from sql import *  # Used for database connection and management
from SarvAuth import *  # Used for user authentication functions
from auth import auth_blueprint
from dictionary_routes import dict_bp as dictionary_blueprint

app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = os.urandom(24)  # Required for flash messages

# Initialize extensions
Session(app)

# Register blueprints
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(dictionary_blueprint, url_prefix='/dictionary')

# Configuration
autoRun = True  # Set to True to run the server automatically when app.py is executed
port = 5000  # Change to any available port
authentication = True  # Set to False to disable authentication

# This route always redirects to the dictionary
@app.route("/", methods=["GET"])
def index():
    return redirect(url_for('dictionary.index'))

if autoRun:
    if __name__ == '__main__':
        app.run(debug=True, port=port)
