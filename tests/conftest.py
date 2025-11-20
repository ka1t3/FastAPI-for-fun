import pytest
from fastapi.testclient import TestClient
import sqlite3
from main import app
from database import get_db

# Override the database dependency for testing
@pytest.fixture(name="client")
def client_fixture():
    # Create an in-memory database for testing
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Initialize the schema
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sujet TEXT NOT NULL,
            contenu TEXT NOT NULL,
            auteur TEXT DEFAULT 'Anonymous',
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            votes INTEGER DEFAULT 0,
            pinned BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()

    # Define the dependency override
    def get_test_db():
        yield conn

    # Apply the override
    app.dependency_overrides[get_db] = get_test_db
    
    # Create the test client
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()
    conn.close()