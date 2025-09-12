import sqlite3
import os

# Create or overwrite the notes database
database = open('notes.db', 'w')
database.truncate(0)  
database.close()

# Connect to the SQLite database
connection = sqlite3.connect("notes.db")
crsr = connection.cursor()

# Define the table structure
create_table_sql = """
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                -- short title for the note
    content TEXT NOT NULL,              -- the full note text
    unit_number INTEGER,                -- optional: to group with course units
    tags TEXT,                          -- comma-separated or JSON for filtering/search
    related_entries TEXT,               -- store glossary ids (e.g., "1,4,5") for cross-linking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views INTEGER DEFAULT 0,            -- track popularity
    is_favorite BOOLEAN DEFAULT 0,      -- quick flag for starred notes
    comments TEXT                       -- optional: your own thoughts or annotations
)
"""

# Create the table
crsr.execute(create_table_sql)

# Create indexes for better performance
crsr.execute("CREATE INDEX idx_notes_unit ON notes(unit_number)")
crsr.execute("CREATE INDEX idx_notes_favorite ON notes(is_favorite)")

# Create trigger for automatic last_updated timestamp
trigger_sql = """
CREATE TRIGGER update_notes_timestamp
AFTER UPDATE ON notes
BEGIN
    UPDATE notes 
    SET last_updated = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
"""

crsr.execute(trigger_sql)

# Commit changes and close the connection
connection.commit()
connection.close()

print("Notes database created successfully with required tables and indexes.")
