import sqlite3
import os
import sys

# Add parent directory to path to import database configuration if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, DATABASE_NAME

SAMPLE_NOTES = [
    {
        "topic": "The Stoic Mindset",
        "content": "We suffer more often in imagination than in reality. - Seneca. A reminder to focus on what we can control.",
        "author": "Marcus",
        "votes": 42,
        "pinned": 1
    },
    {
        "topic": "Python Tips: List Comprehensions",
        "content": "List comprehensions provide a concise way to create lists. Common applications are to make new lists where each element is the result of some operations applied to each member of another sequence.",
        "author": "PyCoder",
        "votes": 15,
        "pinned": 0
    },
    {
        "topic": "Recipe: Perfect Sourdough",
        "content": "The key is a strong starter and patience. Autolyse for 1 hour, bulk ferment for 4-5 hours with stretch and folds every 30 mins.",
        "author": "BakerBob",
        "votes": 8,
        "pinned": 0
    },
    {
        "topic": "Is AI conscious?",
        "content": "Defining consciousness is the hard part. If it mimics human reasoning perfectly, does the distinction matter?",
        "author": "TechPhilosopher",
        "votes": 25,
        "pinned": 1
    },
    {
        "topic": "Gardening 101",
        "content": "Don't overwater your succulents! They thrive on neglect. Wait until the soil is completely dry.",
        "author": "GreenThumb",
        "votes": 3,
        "pinned": 0
    },
    {
        "topic": "Movie Review: Dune Part 2",
        "content": "A visual masterpiece. The scale is breathtaking. Hans Zimmer's score is incredible as always.",
        "author": "Cinephile",
        "votes": 12,
        "pinned": 0
    },
    {
        "topic": "Morning Routine",
        "content": "1. Drink water\n2. Stretch\n3. Read 10 pages\n4. Deep work for 2 hours. Changed my life.",
        "author": "ProductivityGuru",
        "votes": 55,
        "pinned": 0
    },
    {
        "topic": "Random Thought",
        "content": "Why do we press harder on the remote when the batteries are dead?",
        "author": "Anonymous",
        "votes": 1,
        "pinned": 0
    }
]

def init_sample_data():
    # Ensure table exists
    init_db()
    
    print(f"Connecting to {DATABASE_NAME}...")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    print("Clearing existing notes...")
    cursor.execute("DELETE FROM notes")
    
    print("Inserting sample notes...")
    for note in SAMPLE_NOTES:
        cursor.execute('''
            INSERT INTO notes (topic, content, author, votes, pinned)
            VALUES (?, ?, ?, ?, ?)
        ''', (note["topic"], note["content"], note["author"], note["votes"], note["pinned"]))
    
    conn.commit()
    print(f"Successfully inserted {len(SAMPLE_NOTES)} notes.")
    conn.close()

if __name__ == "__main__":
    init_sample_data()