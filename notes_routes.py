from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from sql import SQL
import sqlite3
from datetime import datetime
import re

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

@notes_bp.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    """Edit an existing note"""
    if not session.get("name"):
        return redirect("/auth/login")
    
    db = SQL("sqlite:///notes.db")
    
    # Get the note first to ensure it exists
    note = db.execute("SELECT * FROM notes WHERE id = :id", id=note_id)
    if not note:
        abort(404)
    
    note = note[0]
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        unit_number = request.form.get('unit_number', '').strip()
        tags = request.form.get('tags', '').strip()
        related_entries = request.form.get('related_entries', '').strip()
        comments = request.form.get('comments', '').strip()
        is_favorite = 1 if request.form.get('is_favorite') else 0
        
        # Validate required fields
        if not title or not content:
            flash('Title and content are required', 'error')
            return render_template('notes/edit.html', note={
                'id': note_id,
                'title': title,
                'content': content,
                'unit_number': unit_number,
                'tags': tags,
                'related_entries': related_entries,
                'comments': comments,
                'is_favorite': is_favorite
            })
        
        try:
            unit_number = int(unit_number) if unit_number else None
            
            # Update the note
            db.execute("""
                UPDATE notes 
                SET title = :title,
                    content = :content,
                    unit_number = :unit_number,
                    tags = :tags,
                    related_entries = :related_entries,
                    comments = :comments,
                    is_favorite = :is_favorite,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = :id
            """, 
            id=note_id,
            title=title,
            content=content,
            unit_number=unit_number,
            tags=tags if tags else None,
            related_entries=related_entries if related_entries else None,
            comments=comments if comments else None,
            is_favorite=is_favorite)
            
            flash('Note updated successfully!', 'success')
            return redirect(url_for('notes.view_note', note_id=note_id))
            
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('notes/edit.html', note={
                'id': note_id,
                'title': title,
                'content': content,
                'unit_number': unit_number,
                'tags': tags,
                'related_entries': related_entries,
                'comments': comments,
                'is_favorite': is_favorite
            })
    
    # GET request - show edit form with current note data
    return render_template('notes/edit.html', note=note)

@notes_bp.route('/<int:note_id>')
def view_note(note_id):
    """View a specific note"""
    if not session.get("name"):
        return redirect("/auth/login")
    
    db = SQL("sqlite:///notes.db")
    
    # Get the note
    note = db.execute("""
        SELECT *,
               strftime('%Y-%m-%d', created_at) as created_date,
               strftime('%Y-%m-%d', last_updated) as last_updated
        FROM notes 
        WHERE id = :id
    """, id=note_id)
    
    if not note:
        abort(404)
    
    note = note[0]
    
    # Increment view count
    db.execute("""
        UPDATE notes 
        SET views = COALESCE(views, 0) + 1 
        WHERE id = :id
    """, id=note_id)
    
    # Parse content for markdown-like formatting
    content = note['content']
    
    # Convert markdown headers to HTML
    content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    
    # Convert bold and italic
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    
    # Convert lists
    content = re.sub(r'^\s*[-*] (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', content, flags=re.DOTALL)
    
    # Convert blockquotes
    content = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)
    
    # Convert line breaks to <br> tags
    content = content.replace('\n', '<br>')
    
    # Handle asides (Notion-style callouts)
    content = re.sub(
        r'<aside>\s*💡\s*(.*?)\s*</aside>', 
        r'<div class="callout"><div class="callout-emoji">💡</div><div class="callout-content">\1</div></div>', 
        content, 
        flags=re.DOTALL
    )
    
    # Split content into sections based on headers
    sections = re.split(r'(<h[1-3]>.*?</h[1-3]>)', content)
    
    # Process each section to ensure proper HTML structure
    processed_sections = []
    for i, section in enumerate(sections):
        if section.startswith('<h'):
            # This is a header, add it to the processed sections
            processed_sections.append(section)
        elif section.strip():
            # This is content, wrap it in a paragraph if it's not already in a block element
            if not any(tag in section for tag in ['<p>', '<ul>', '<ol>', '<blockquote>', '<div class="callout">']):
                section = f'<p>{section}</p>'
            processed_sections.append(section)
    
    # Join the sections back together
    processed_content = '\n'.join(processed_sections)
    
    # Get related entries if any
    related_entries = []
    if note.get('related_entries'):
        entry_ids = [int(id_str.strip()) for id_str in note['related_entries'].split(',') if id_str.strip().isdigit()]
        if entry_ids:
            related_entries = db.execute("""
                SELECT id, word_phrase 
                FROM dictionary.entries 
                WHERE id IN ({})
            """.format(','.join('?' * len(entry_ids))), *entry_ids)
    
    return render_template('notes/view.html', 
                         note=note, 
                         content=processed_content,
                         related_entries=related_entries)

def init_app(app):
    app.register_blueprint(notes_bp)
