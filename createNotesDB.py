import sqlite3
from datetime import datetime

def create_notes_database():
    """
    Creates a new SQLite database for notes with the specified schema.
    """
    try:
        # Connect to SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Create the notes table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notes (
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
        
        cursor.execute(create_table_sql)
        
        # Create an index for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_unit ON notes(unit_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_favorite ON notes(is_favorite)")
        
        # Save (commit) the changes
        conn.commit()
        print("Successfully created notes database with schema.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_trigger_for_last_updated():
    """
    Adds a trigger to automatically update the last_updated timestamp
    when a note is modified.
    """
    try:
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        
        # Create a trigger to update last_updated timestamp
        trigger_sql = """
        CREATE TRIGGER IF NOT EXISTS update_notes_timestamp
        AFTER UPDATE ON notes
        BEGIN
            UPDATE notes 
            SET last_updated = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
        
        cursor.execute(trigger_sql)
        conn.commit()
        print("Successfully added update trigger for notes.")
        return True
        
    except sqlite3.Error as e:
        print(f"Error creating trigger: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if create_notes_database():
        if add_trigger_for_last_updated():
            print("Notes database setup completed successfully!")
        else:
            print("Notes database created, but there was an issue adding the update trigger.")
    else:
        print("Failed to create notes database.")
