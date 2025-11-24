import sqlite3

DATABASE_NAME = "agora.db"

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize the database with the notes table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            votes INTEGER DEFAULT 0,
            pinned BOOLEAN DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Dependency for database connections."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()