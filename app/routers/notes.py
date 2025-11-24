from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import List, Optional
from app.core.database import get_db
from app.models.models import NoteCreate, NoteUpdate, NoteResponse
from app.core.security import get_api_key
from app.core.limiter import limiter
import sqlite3

router = APIRouter(tags=["Notes"])

@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=201,
    summary="Create a new note",
    description="Add a new note to the Agora. You can optionally provide an author name."
)
@limiter.limit("10/minute")
def create_note(request: Request, note: NoteCreate, conn=Depends(get_db)):
    """
    Create a new note with the following information:
    
    - **topic**: The topic of the note
    - **content**: The main content
    - **author**: (Optional) The author's nickname (defaults to 'Anonymous')
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (topic, content, author) VALUES (?, ?, ?)",
        (note.topic, note.content, note.author)
    )
    note_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the created note
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    new_note = cursor.fetchone()
    return dict(new_note)

@router.get(
    "/notes",
    response_model=List[NoteResponse],
    summary="List all notes",
    description="Retrieve a list of notes with optional filtering and searching."
)
@limiter.limit("100/minute")
def read_notes(
    request: Request,
    topic: Optional[str] = Query(None, description="Filter by exact topic"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    search: Optional[str] = Query(None, description="Search for keywords in the content"),
    conn=Depends(get_db)
):
    query = "SELECT * FROM notes WHERE 1=1"
    params = []

    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if author:
        query += " AND author = ?"
        params.append(author)
    if search:
        query += " AND content LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY created_at DESC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    notes = cursor.fetchall()
    return [dict(note) for note in notes]

@router.get(
    "/notes/top",
    response_model=List[NoteResponse],
    summary="Get top voted notes",
    description="Retrieve the top 10 notes with the highest number of votes."
)
def get_top_notes(conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY votes DESC LIMIT 10")
    notes = cursor.fetchall()
    return [dict(note) for note in notes]

@router.get(
    "/notes/{note_id}",
    response_model=NoteResponse,
    summary="Get a specific note",
    description="Retrieve details of a specific note by its ID."
)
def read_note(note_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return dict(note)

@router.put(
    "/notes/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update the topic, content, or author of an existing note."
)
def update_note(note_id: int, note_update: NoteUpdate, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    # Check if note exists
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    existing_note = cursor.fetchone()
    if existing_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    if note_update.topic is not None:
        update_fields.append("topic = ?")
        params.append(note_update.topic)
    if note_update.content is not None:
        update_fields.append("content = ?")
        params.append(note_update.content)
    if note_update.author is not None:
        update_fields.append("author = ?")
        params.append(note_update.author)
        
    if not update_fields:
        return dict(existing_note)
        
    params.append(note_id)
    query = f"UPDATE notes SET {', '.join(update_fields)} WHERE id = ?"
    
    cursor.execute(query, params)
    conn.commit()
    
    # Return updated note
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    updated_note = cursor.fetchone()
    return dict(updated_note)

@router.post(
    "/notes/{note_id}/pin",
    response_model=NoteResponse,
    summary="Pin a note",
    description="Mark a note as pinned to highlight it."
)
def pin_note(note_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    # Check if note exists
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Note not found")
        
    cursor.execute("UPDATE notes SET pinned = 1 WHERE id = ?", (note_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    updated_note = cursor.fetchone()
    return dict(updated_note)

@router.delete(
    "/notes/{note_id}",
    summary="Delete a note",
    description="Permanently remove a note. **Requires Admin API Key**.",
    responses={403: {"description": "Not authenticated"}}
)
def delete_note(note_id: int, conn=Depends(get_db), api_key: str = Depends(get_api_key)):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    conn.commit()
    return {"message": "Note deleted successfully"}

@router.post(
    "/notes/{note_id}/vote",
    response_model=NoteResponse,
    summary="Vote for a note",
    description="Increment the vote count for a specific note."
)
def vote_note(note_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    
    # Check if note exists
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Note not found")
        
    cursor.execute("UPDATE notes SET votes = votes + 1 WHERE id = ?", (note_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    updated_note = cursor.fetchone()
    return dict(updated_note)