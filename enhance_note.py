import os
import sqlite3
import time
import google.generativeai as genai
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY in your .env file")

# Configure the API key
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.0 Flash-Lite
model_name = 'gemini-2.0-flash-lite'
print(f"Using model: {model_name}")
model = genai.GenerativeModel(model_name)

# Rate limiting settings
RATE_LIMIT_DELAY = 5  # seconds between requests
last_request_time = 0

def get_db_connection(db_path):
    """Create and return a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_note(note_id):
    """Retrieve a single note by ID from the database."""
    db_path = os.path.join(os.path.dirname(__file__), 'notes.db')
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, title, content FROM notes WHERE id = ?", (note_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def enhance_note_content(title, content):
    """Use Gemini to enhance the note content while preserving its structure."""
    system_prompt = """
    You are a legal expert and educator. Your task is to enhance legal notes while preserving their structure and core concepts.
    For each note:
    1. Keep the original structure and key points
    2. Improve clarity and flow
    3. Add relevant examples or case law where appropriate
    4. Include related legal principles or exceptions
    5. Use clear, concise language
    6. Maintain any existing formatting like lists or sections
    7. Add "Key Concepts" and "Practical Applications" sections if missing
    """
    
    global last_request_time
    
    # Rate limiting
    time_since_last = time.time() - last_request_time
    if time_since_last < RATE_LIMIT_DELAY:
        sleep_time = RATE_LIMIT_DELAY - time_since_last
        print(f"  ⏳ Rate limiting: Waiting {sleep_time:.1f} seconds...")
        time.sleep(sleep_time)
    
    last_request_time = time.time()
    
    try:
        # Combine system prompt and user content
        full_prompt = f"""{system_prompt}
        
        Title: {title}
        
        Current Content:
        {content}
        
        Please enhance this note while preserving its structure and key points.
        Keep the original formatting and structure intact.
        """
        
        print(f"  Processing with {model_name}...")
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,  # Slightly more focused responses
                max_output_tokens=2000,
                top_p=0.8,
                top_k=32
            )
        )
        
        if not response.text:
            raise ValueError("Empty response from model")
            
        return response.text.strip()
        
    except Exception as e:
        print(f"  ❌ Error enhancing note: {str(e)}")
        return None

def update_note(note_id, enhanced_content):
    """Update the note in the database with enhanced content."""
    db_path = os.path.join(os.path.dirname(__file__), 'notes.db')
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE notes SET content = ? WHERE id = ?",
            (enhanced_content, note_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"  ❌ Error updating note: {str(e)}")
        return False
    finally:
        conn.close()

def backup_notes():
    """Create a backup of the notes database."""
    import shutil
    from datetime import datetime
    
    db_path = os.path.join(os.path.dirname(__file__), 'notes.db')
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'notes_backup_{timestamp}.db')
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup at: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Enhance a single note using AI')
    parser.add_argument('note_id', type=int, help='ID of the note to enhance')
    parser.add_argument('--preview', action='store_true', help='Show preview without saving changes')
    args = parser.parse_args()
    
    print(f"🔍 Fetching note with ID: {args.note_id}")
    note = get_note(args.note_id)
    
    if not note:
        print(f"❌ No note found with ID: {args.note_id}")
        return
    
    print(f"📝 Note found: {note['title']}")
    
    # Create a backup before making changes
    if not args.preview:
        print("\n💾 Creating backup of notes database...")
        if not backup_notes():
            print("⚠️  Proceeding without backup")
    
    print("\n🤖 Enhancing note content...")
    enhanced_content = enhance_note_content(note['title'], note['content'])
    
    if not enhanced_content:
        print("❌ Failed to enhance note")
        return
    
    if args.preview:
        print("\n✨ Enhanced Content (Preview - not saved):")
        print("=" * 80)
        print(enhanced_content)
        print("=" * 80)
        print("\nNote: Run without --preview to save changes")
    else:
        if update_note(note['id'], enhanced_content):
            print("\n✅ Note enhanced successfully!")
        else:
            print("\n❌ Failed to update note")

if __name__ == "__main__":
    main()
