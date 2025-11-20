import sqlite3
import os
import sys

# Add parent directory to path to import database configuration if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, DATABASE_NAME

SAMPLE_NOTES = [
    {
        "sujet": "The Stoic Mindset",
        "contenu": "We suffer more often in imagination than in reality. - Seneca. A reminder to focus on what we can control.",
        "auteur": "Marcus",
        "votes": 42,
        "pinned": 1
    },
    {
        "sujet": "Python Tips: List Comprehensions",
        "contenu": "List comprehensions provide a concise way to create lists. Common applications are to make new lists where each element is the result of some operations applied to each member of another sequence.",
        "auteur": "PyCoder",
        "votes": 15,
        "pinned": 0
    },
    {
        "sujet": "Recipe: Perfect Sourdough",
        "contenu": "The key is a strong starter and patience. Autolyse for 1 hour, bulk ferment for 4-5 hours with stretch and folds every 30 mins.",
        "auteur": "BakerBob",
        "votes": 8,
        "pinned": 0
    },
    {
        "sujet": "Is AI conscious?",
        "contenu": "Defining consciousness is the hard part. If it mimics human reasoning perfectly, does the distinction matter?",
        "auteur": "TechPhilosopher",
        "votes": 25,
        "pinned": 1
    },
    {
        "sujet": "Gardening 101",
        "contenu": "Don't overwater your succulents! They thrive on neglect. Wait until the soil is completely dry.",
        "auteur": "GreenThumb",
        "votes": 3,
        "pinned": 0
    },
    {
        "sujet": "Movie Review: Dune Part 2",
        "contenu": "A visual masterpiece. The scale is breathtaking. Hans Zimmer's score is incredible as always.",
        "auteur": "Cinephile",
        "votes": 12,
        "pinned": 0
    },
    {
        "sujet": "Morning Routine",
        "contenu": "1. Drink water\n2. Stretch\n3. Read 10 pages\n4. Deep work for 2 hours. Changed my life.",
        "auteur": "ProductivityGuru",
        "votes": 55,
        "pinned": 0
    },
    {
        "sujet": "Random Thought",
        "contenu": "Why do we press harder on the remote when the batteries are dead?",
        "auteur": "Anonymous",
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
            INSERT INTO notes (sujet, contenu, auteur, votes, pinned)
            VALUES (?, ?, ?, ?, ?)
        ''', (note["sujet"], note["contenu"], note["auteur"], note["votes"], note["pinned"]))
    
    conn.commit()
    print(f"Successfully inserted {len(SAMPLE_NOTES)} notes.")
    conn.close()

if __name__ == "__main__":
    init_sample_data()