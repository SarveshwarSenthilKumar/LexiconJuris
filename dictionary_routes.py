from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort
from sql import SQL
import sqlite3
from datetime import datetime
import re

# Initialize Blueprint
dict_bp = Blueprint('dictionary', __name__, url_prefix='/dictionary')

def get_related_terms(word_phrase, current_id=None, limit=5):
    """Find related terms based on word similarity"""
    if not word_phrase:
        return []
    
    # Extract keywords (simple approach - split by spaces and common separators)
    keywords = re.findall(r'\b\w+\b', word_phrase.lower())
    if not keywords:
        return []
    
    # Build a query to find related terms
    db = SQL("sqlite:///dictionary.db")
    
    # Create a list to hold conditions and params
    conditions = []
    params = {}
    
    # Add conditions for each keyword
    for i, keyword in enumerate(keywords[:3]):  # Limit to first 3 keywords
        if len(keyword) > 2:  # Only consider words longer than 2 characters
            conditions.append(f"(word_phrase LIKE :kw{i} OR definition LIKE :kw{i})")
            params[f'kw{i}'] = f'%{keyword}%'
    
    if not conditions:
        return []
    
    # Build the query
    query = """
        SELECT id, word_phrase, definition, 
               (SELECT COUNT(*) FROM entries e2 WHERE e2.id != entries.id 
                AND (e2.word_phrase LIKE '%' || entries.word_phrase || '%' 
                     OR entries.word_phrase LIKE '%' || e2.word_phrase || '%')) as relevance
        FROM entries
        WHERE (""" + " OR ".join(conditions) + ")"
    
    if current_id:
        query += " AND id != :current_id"
        params['current_id'] = current_id
    
    query += """
        GROUP BY id
        ORDER BY relevance DESC, LENGTH(word_phrase) ASC
        LIMIT :limit
    """
    
    params['limit'] = limit
    
    try:
        return db.execute(query, **params)
    except Exception as e:
        current_app.logger.error(f"Error finding related terms: {str(e)}")
        return []

@dict_bp.route('')
def index():
    if not session.get("name"):
        return redirect("/auth/login")
    
    db = SQL("sqlite:///dictionary.db")
    entries = db.execute("""
        SELECT id, word_phrase, definition, example, views, 
               strftime('%Y-%m-%d', created_at) as created_date
        FROM entries 
        ORDER BY word_phrase ASC
    """)
    return render_template("dictionary/index.html", entries=entries)

@dict_bp.route('/add', methods=['GET', 'POST'])
def add_entry():
    if not session.get("name"):
        return redirect("/auth/login")
        
    if request.method == 'POST':
        word_phrase = request.form.get('word_phrase', '').strip()
        definition = request.form.get('definition', '').strip()
        example = request.form.get('example', '').strip()
        
        if not word_phrase or not definition:
            flash('Word/Phrase and Definition are required', 'error')
            return render_template('dictionary/add.html', 
                                word_phrase=word_phrase,
                                definition=definition,
                                example=example)
        
        try:
            db = SQL("sqlite:///dictionary.db")
            db.execute("""
                INSERT INTO entries (word_phrase, definition, example)
                VALUES (:word_phrase, :definition, :example)
            """, word_phrase=word_phrase, definition=definition, example=example)
            
            flash('Entry added successfully!', 'success')
            return redirect(url_for('dictionary.index'))
            
        except sqlite3.IntegrityError:
            flash('This word/phrase already exists in the dictionary', 'error')
            return render_template('dictionary/add.html',
                                word_phrase=word_phrase,
                                definition=definition,
                                example=example)
    
    return render_template('dictionary/add.html')

@dict_bp.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    if not session.get("name"):
        return redirect("/auth/login")
        
    db = SQL("sqlite:///dictionary.db")
    
    try:
        # Increment view count
        db.execute("""
            UPDATE entries 
            SET views = COALESCE(views, 0) + 1 
            WHERE id = :id
        """, id=entry_id)
        
        # Get the entry
        entry = db.execute("""
            SELECT id, word_phrase, definition, example, views, 
                   strftime('%Y-%m-%d', created_at) as created_date,
                   strftime('%Y-%m-%d', last_updated) as last_updated
            FROM entries 
            WHERE id = :id
        """, id=entry_id)
        
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('dictionary.index'))
            
        # Get related terms
        related_terms = get_related_terms(entry[0]['word_phrase'], entry_id)
        
        return render_template('dictionary/entry.html', 
                             entry=entry[0], 
                             related_terms=related_terms)
    except Exception as e:
        current_app.logger.error(f"Error viewing entry {entry_id}: {str(e)}")
        flash('An error occurred while loading the entry', 'error')
        return redirect(url_for('dictionary.index'))

@dict_bp.route('/entry/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if not session.get("name"):
        return redirect("/auth/login")
        
    db = SQL("sqlite:///dictionary.db")
    
    # Get the existing entry
    entry = db.execute("""
        SELECT id, word_phrase, definition, example 
        FROM entries 
        WHERE id = :id
    """, id=entry_id)
    
    if not entry:
        flash('Entry not found', 'error')
        return redirect(url_for('dictionary.index'))
        
    entry = entry[0]
    
    if request.method == 'POST':
        try:
            word_phrase = request.form.get('word_phrase', '').strip()
            definition = request.form.get('definition', '').strip()
            example = request.form.get('example', '').strip()
            
            if not word_phrase or not definition:
                flash('Word/phrase and definition are required', 'error')
                return redirect(url_for('dictionary.edit_entry', entry_id=entry_id))
            
            # Update the entry
            db.execute("""
                UPDATE entries 
                SET word_phrase = :word_phrase,
                    definition = :definition,
                    example = :example,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = :id
            """, 
            word_phrase=word_phrase,
            definition=definition,
            example=example if example else None,
            id=entry_id)
            
            flash('Entry updated successfully!', 'success')
            return redirect(url_for('dictionary.view_entry', entry_id=entry_id))
            
        except Exception as e:
            current_app.logger.error(f"Error updating entry {entry_id}: {str(e)}")
            flash('An error occurred while updating the entry', 'error')
            return redirect(url_for('dictionary.edit_entry', entry_id=entry_id))
    
    return render_template('dictionary/edit.html', entry=entry)

@dict_bp.route('/search')
def search():
    if not session.get("name"):
        return redirect("/auth/login")
        
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('dictionary.index'))
        
    try:
        db = SQL("sqlite:///dictionary.db")
        
        # Split query into keywords
        keywords = re.findall(r'\b\w+\b', query.lower())
        
        # Build the search query with ranking
        search_query = """
            SELECT id, word_phrase, definition, example, views, 
                   strftime('%Y-%m-%d', created_at) as created_date,
                   (
                       -- Exact match
                       (CASE WHEN word_phrase = :exact_query THEN 4 ELSE 0 END) +
                       -- Starts with
                       (CASE WHEN word_phrase LIKE :starts_with THEN 3 ELSE 0 END) +
                       -- Contains all keywords
                       (CASE WHEN """ + " AND ".join(["(word_phrase LIKE ? OR definition LIKE ?)" for _ in keywords]) + """ THEN 2 ELSE 0 END) +
                       -- Contains any keyword
                       (CASE WHEN """ + " OR ".join(["(word_phrase LIKE ? OR definition LIKE ?)" for _ in keywords]) + """ THEN 1 ELSE 0 END)
                   ) as relevance
            FROM entries
            WHERE 1=1
        """
        
        # Add search conditions
        params = {
            'exact_query': query,
            'starts_with': f"{query}%"
        }
        
        # Add parameters for each keyword (twice - once for word_phrase, once for definition)
        for kw in keywords:
            params[f'kw_{kw}'] = f'%{kw}%'
            params[f'kw_def_{kw}'] = f'%{kw}%'
        
        # Add ORDER BY and LIMIT
        search_query += """
            ORDER BY relevance DESC, word_phrase ASC
            LIMIT 50
        """
        
        # Execute the query with all parameters
        entries = db.execute(search_query, 
                           exact_query=query,
                           starts_with=f"{query}%",
                           **{k: v for k, v in params.items() if k.startswith('kw_')})
        
        return render_template('dictionary/search.html', 
                             entries=entries, 
                             query=query)
                             
    except Exception as e:
        current_app.logger.error(f"Search error for '{query}': {str(e)}")
        flash('An error occurred during search', 'error')
        return redirect(url_for('dictionary.index'))
