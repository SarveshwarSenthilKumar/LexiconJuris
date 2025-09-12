from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sql import SQL
import sqlite3
from datetime import datetime

# Initialize Blueprint
notes_bp = Blueprint('notes', __name__, url_prefix='/notes')

@notes_bp.route('')
def index():
    """Display all notes"""
    if not session.get("name"):
        return redirect("/auth/login")
    
    db = SQL("sqlite:///notes.db")
    notes = db.execute("""
        SELECT id, title, unit_number, 
               strftime('%Y-%m-%d', created_at) as created_date,
               strftime('%Y-%m-%d', last_updated) as last_updated,
               is_favorite
        FROM notes 
        ORDER BY last_updated DESC
    """)
    
    # Group notes by unit number for better organization
    notes_by_unit = {}
    for note in notes:
        unit = note.get('unit_number', 'Ungrouped')
        if unit not in notes_by_unit:
            notes_by_unit[unit] = []
        notes_by_unit[unit].append(note)
    
    return render_template('notes/index.html', 
                         notes_by_unit=notes_by_unit)

@notes_bp.route('/add', methods=['GET', 'POST'])
def add_note():
    """Add a new note"""
    if not session.get("name"):
        return redirect("/auth/login")
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        unit_number = request.form.get('unit_number', '').strip()
        tags = request.form.get('tags', '').strip()
        related_entries = request.form.get('related_entries', '').strip()
        comments = request.form.get('comments', '').strip()
        is_favorite = 1 if request.form.get('is_favorite') else 0
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('notes/add.html',
                                title=title,
                                content=content,
                                unit_number=unit_number,
                                tags=tags,
                                related_entries=related_entries,
                                comments=comments,
                                is_favorite=is_favorite)
        
        try:
            unit_number = int(unit_number) if unit_number else None
            
            db = SQL("sqlite:///notes.db")
            db.execute("""
                INSERT INTO notes (title, content, unit_number, tags, 
                                 related_entries, comments, is_favorite)
                VALUES (:title, :content, :unit_number, :tags, 
                       :related_entries, :comments, :is_favorite)
            """, 
            title=title,
            content=content,
            unit_number=unit_number,
            tags=tags if tags else None,
            related_entries=related_entries if related_entries else None,
            comments=comments if comments else None,
            is_favorite=is_favorite)
            
            flash('Note added successfully!', 'success')
            return redirect(url_for('notes.index'))
            
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('notes/add.html',
                                title=title,
                                content=content,
                                unit_number=unit_number,
                                tags=tags,
                                related_entries=related_entries,
                                comments=comments,
                                is_favorite=is_favorite)
    
    return render_template('notes/add.html')

def init_app(app):
    app.register_blueprint(notes_bp)
