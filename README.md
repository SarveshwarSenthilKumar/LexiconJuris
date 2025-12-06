# LexiconJuris

A comprehensive web application for legal professionals and students to manage legal terms, case notes, and case law references with advanced search capabilities and user authentication.

## Features

### 1. Legal Dictionary
- Add, edit, and search legal terms and definitions
- View entry history and related terms
- Public and private entry views
- Advanced search with filtering options

### 2. Case Notes Management
- (Work in Progress)
- Create and organize case notes
- Rich text formatting support
- Tagging and categorization
- Full-text search across all notes

### 3. Calendar Integration
- Track important legal dates and deadlines
- Set reminders for court dates and filings
- View calendar by day, week, or month

### 4. User Authentication & Security
- Secure user registration and login
- Role-based access control
- Session management
- Password hashing with salt

## Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Custom authentication system with session management
- **Templates**: Jinja2

### Frontend
- HTML5, CSS3, JavaScript
- Responsive design
- Interactive UI components

### Dependencies
- See [requirements.txt](requirements.txt) for complete list

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SarveshwarSenthilKumar/LexiconJuris.git
   cd LexiconJuris
   ```

2. **Set up a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///users.db
   ```

5. **Initialize the database**
   ```bash
   python createDatabase.py
   python createDictDB.py
   python createNotesDB.py
   python createCalendarDB.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your web browser and navigate to `http://localhost:5000`

## Project Structure

```
LexiconJuris/
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── static/                # Static files (CSS, JS, images)
├── templates/             # HTML templates
├── auth.py                # Authentication routes
├── dictionary_routes.py   # Dictionary functionality
├── notes_routes.py        # Notes management
├── calendar_routes.py     # Calendar functionality
├── sql.py                 # Database utilities
├── createDatabase.py      # Database initialization
└── README.md              # This file
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Dictionary
- `GET /dictionary` - View all entries
- `POST /dictionary/add` - Add new entry
- `GET /dictionary/<int:entry_id>` - View specific entry
- `POST /dictionary/<int:entry_id>/edit` - Edit entry
- `POST /dictionary/<int:entry_id>/delete` - Delete entry
- `GET /dictionary/search` - Search entries

### Notes
- `GET /notes` - View all notes
- `POST /notes/add` - Add new note
- `GET /notes/<int:note_id>` - View specific note
- `POST /notes/<int:note_id>/edit` - Edit note
- `POST /notes/<int:note_id>/delete` - Delete note

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Built with Flask
- Uses SQLite for database
- Inspired by the needs of legal professionals