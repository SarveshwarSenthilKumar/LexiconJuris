from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from sql import SQL
import random

# Initialize Blueprint
test_bp = Blueprint('tests', __name__, url_prefix='/tests')

def generate_definition_question(word, definition):
    """Generate a definition-based question"""
    question = f"What is the definition of '{word}'?"
    return {
        'type': 'definition',
        'question': question,
        'answer': definition,
        'options': []
    }

def generate_example_question(word, example):
    """Generate an example usage question"""
    if not example:
        return None
        
    # Replace the word/phrase with a blank in the example
    blanked_example = example.replace(word, '__________')
    question = f"Complete the following sentence: {blanked_example}"
    
    return {
        'type': 'fill_blank',
        'question': question,
        'answer': word,
        'options': []
    }

def generate_mcq_question(word, definition, all_definitions):
    """Generate a multiple-choice question"""
    if len(all_definitions) < 3:
        return None
        
    # Get 3 random incorrect definitions
    other_definitions = [d for d in all_definitions if d != definition]
    if len(other_definitions) > 3:
        other_definitions = random.sample(other_definitions, 3)
    
    options = [definition] + other_definitions
    random.shuffle(options)
    
    return {
        'type': 'multiple_choice',
        'question': f"What is the correct definition of '{word}'?",
        'answer': definition,
        'options': options
    }

@test_bp.route('/generate/<int:unit_number>')
def generate_test(unit_number):
    if not session.get("name"):
        return redirect(url_for('auth.login', next=request.url))
    
    try:
        print(f"\n=== Starting test generation for unit {unit_number} ===")
        print("Current user:", session.get("name"))
        # Connect to both databases
        dict_db = SQL("sqlite:///dictionary.db")
        notes_db = SQL("sqlite:///notes.db")
        
        # Get dictionary entries for the unit
        print("Fetching dictionary entries...")
        dictionary_entries = dict_db.execute("""
            SELECT id, word_phrase, definition, example, unit_number
            FROM entries 
            WHERE unit_number = :unit_number
            ORDER BY RANDOM()
            LIMIT 20  # Limit to 20 terms to keep the test manageable
        """, unit_number=unit_number)
        print(f"Found {len(dictionary_entries)} dictionary entries")
        
        # Get notes for the unit
        print("Fetching notes...")
        notes = notes_db.execute("""
            SELECT id, title, content, unit_number
            FROM notes
            WHERE unit_number = :unit_number
            ORDER BY RANDOM()
            LIMIT 5  # Limit to 5 notes to keep the test focused
        """, unit_number=unit_number)
        print(f"Found {len(notes)} notes")
        
        # Generate test questions from dictionary entries
        test_questions = []
        all_definitions = [entry['definition'] for entry in dictionary_entries]
        
        print(f"Generating questions from {len(dictionary_entries)} dictionary entries...")
        for entry in dictionary_entries:
            # Add definition question
            test_questions.append(generate_definition_question(
                entry['word_phrase'], 
                entry['definition']
            ))
            
            # Add example question if available
            if entry.get('example'):
                example_q = generate_example_question(
                    entry['word_phrase'],
                    entry['example']
                )
                if example_q:
                    test_questions.append(example_q)
            
            # Add multiple choice question if we have enough definitions
            mcq = generate_mcq_question(
                entry['word_phrase'],
                entry['definition'],
                all_definitions
            )
            if mcq:
                test_questions.append(mcq)
        
        # Add questions from notes (simple recall questions)
        print(f"Generating questions from {len(notes)} notes...")
        for note in notes:
            # Simple question based on note title
            test_questions.append({
                'type': 'short_answer',
                'question': f"What are the key points about '{note['title']}'?",
                'answer': note['content'],
                'options': []
            })
        
        # Shuffle the questions
        random.shuffle(test_questions)
        
        # Limit to 15 questions total
        test_questions = test_questions[:15]
        
        print(f"\n=== DEBUG: Generated {len(test_questions)} questions ===")
        
        # Debug: Print all questions
        for i, q in enumerate(test_questions):
            print(f"Question {i+1} (Type: {q['type']}): {q['question'][:100]}...")
            if 'options' in q and q['options']:
                print(f"  Options: {q['options']}")
        
        # Use forward slashes for template path (Jinja2 uses forward slashes on all platforms)
        template_path = 'tests/generate.html'
        print(f"\n=== DEBUG: Attempting to render template: {template_path}")
        
        # Debug: Check if template exists and can be rendered
        from flask import current_app, render_template_string
        with current_app.app_context():
            try:
                # Test template rendering with a simple string
                test_render = render_template_string('Test template rendering: {{ test_var }}', test_var='SUCCESS')
                print(f"Template rendering test: {test_render}")
                
                # Try to get the actual template
                template = current_app.jinja_env.get_or_select_template(template_path)
                print("Template found and loaded successfully")
                
                # Try rendering with test data
                test_data = [
                    {
                        'type': 'test',
                        'question': 'Test question',
                        'answer': 'Test answer',
                        'options': []
                    }
                ]
                test_output = render_template(template_path, 
                                          test_questions=test_data,
                                          unit_number=unit_number)
                print(f"Test render successful. Output length: {len(test_output) if test_output else 0} characters")
                
            except Exception as e:
                print(f"\n=== TEMPLATE ERROR ===")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("====================\n")
                raise
        
        # Render the actual template
        print("\n=== Rendering actual template with real data ===")
        return render_template(template_path,
                             test_questions=test_questions,
                             unit_number=unit_number)
                             
    except Exception as e:
        import traceback
        error_msg = f'Error generating test: {str(e)}\n\n{traceback.format_exc()}'
        print("\n" + "="*50)
        print("ERROR IN TEST GENERATION:")
        print(error_msg)
        print("="*50 + "\n")
        flash('Error generating test. Please check the server logs for details.', 'error')
        return redirect(url_for('dictionary.index'))

def init_app(app):
    # Register the blueprint with the app
    app.register_blueprint(test_bp)
    return test_bp
