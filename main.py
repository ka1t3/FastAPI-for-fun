# uvicorn main:app --reload
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from routers import notes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield
    # Clean up resources on shutdown (if any)

app = FastAPI(
    title="The Knowledge Agora API",
    description="""
    Welcome to **The Knowledge Agora**, a collaborative micro-blogging platform.
    
    ## Features
    * **Create Notes**: Share your thoughts anonymously or with a nickname.
    * **Read & Search**: Browse notes, filter by author/topic, or search content.
    * **Vote**: Upvote the most interesting notes.
    * **Pin**: Highlight important notes.
    * **Manage**: Update or delete notes (Admin only).
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Agora Admin",
        "email": "admin@agora.com",
    },
    license_info={
        "name": "MIT",
    }
)

# Include routers
app.include_router(notes.router)

@app.get("/")
def read_root():
    """Welcome message and instructions."""
    return {
        "message": "Welcome to The Knowledge Agora API",
        "docs": "/docs",
        "endpoints": {
            "list_notes": "GET /notes",
            "create_note": "POST /notes",
            "read_note": "GET /notes/{id}",
            "update_note": "PUT /notes/{id}",
            "delete_note": "DELETE /notes/{id}",
            "vote_note": "POST /notes/{id}/vote",
            "top_notes": "GET /notes/top"
        }
    }