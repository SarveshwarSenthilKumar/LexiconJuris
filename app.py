
from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
from flask_session import Session
from datetime import datetime
import pytz
import os
import re
from sql import *  # Used for database connection and management
from SarvAuth import *  # Used for user authentication functions
from auth import auth_blueprint
from dictionary_routes import dict_bp as dictionary_blueprint
from notes_routes import notes_bp as notes_blueprint

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
app.register_blueprint(notes_blueprint, url_prefix='/notes')

# Configuration
autoRun = True  # Set to True to run the server automatically when app.py is executed
port = 5000  # Change to any available port
authentication = True  # Set to False to disable authentication

# This route always redirects to the dictionary
@app.route("/", methods=["GET"])
def index():
    return redirect(url_for('dictionary.index'))

@app.route('/search')
def search():
    """Unified search across dictionary and notes"""
    query = request.args.get('q', '').strip()
    
    dictionary_results = []
    notes_results = []
    
    if query:
        # Clean and prepare the query
        clean_query = ' '.join(word for word in query.split() if len(word) > 2)
        if not clean_query:
            return render_template('search.html',
                               query=query,
                               dictionary_results=[],
                               notes_results=[])
        
        # Search in dictionary
        try:
            db = SQL("sqlite:///dictionary.db")
            
            # Use a simple LIKE query that works with the existing schema
            dict_query = """
                SELECT id, word_phrase, 
                       substr(definition, 1, 200) || '...' as definition
                FROM entries
                WHERE LOWER(word_phrase) LIKE LOWER(:query) 
                   OR LOWER(definition) LIKE LOWER(:query)
                LIMIT 10
            """
            dictionary_results = db.execute(dict_query, query=f"%{clean_query}%")
                    
        except Exception as e:
            app.logger.error(f"Error searching dictionary: {str(e)}")
            dictionary_results = []
        
        # Search in notes
        try:
            db = SQL("sqlite:///notes.db")
            
            # Use a simple LIKE query that works with the existing schema
            notes_query = """
                SELECT id, title, 
                       substr(content, 1, 200) || '...' as content
                FROM notes
                WHERE LOWER(title) LIKE LOWER(:query) 
                   OR LOWER(content) LIKE LOWER(:query)
                LIMIT 10
            """
            notes_results = db.execute(notes_query, query=f"%{clean_query}%")
                    
        except Exception as e:
            app.logger.error(f"Error searching notes: {str(e)}")
            notes_results = []
    
    # Highlight the search terms in the results
    for result in dictionary_results:
        if 'word_phrase' in result:
            result['word_phrase'] = highlight_text(result['word_phrase'], clean_query)
        if 'definition' in result and result['definition']:
            result['definition'] = highlight_text(result['definition'], clean_query)
    
    for result in notes_results:
        if 'title' in result:
            result['title'] = highlight_text(result['title'], clean_query)
        if 'content' in result and result['content']:
            result['content'] = highlight_text(result['content'], clean_query)
    
    return render_template('search.html',
                         query=query,
                         dictionary_results=dictionary_results,
                         notes_results=notes_results)

def highlight_text(text, query):
    """Highlight search terms in the text"""
    if not text or not query:
        return text or ''
    
    try:
        # Escape special regex characters in the query
        query = re.escape(query)
        # Create a case-insensitive regex pattern
        pattern = re.compile(f'({query})', re.IGNORECASE)
        # Replace matches with highlighted span
        return pattern.sub(r'<span class="highlight">\1</span>', text)
    except Exception as e:
        app.logger.error(f"Error highlighting text: {str(e)}")
        return text

# Add a custom filter to highlight text in search results
@app.template_filter('highlight')
def highlight_filter(s, query):
    if not query or not s:
        return s
    try:
        query = re.escape(query)
        return re.sub(f'({query})', 
                     r'<span class="highlight">\1</span>', 
                     s, 
                     flags=re.IGNORECASE)
    except:
        return s

if autoRun:
    if __name__ == '__main__':
        app.run(debug=True, port=port)
