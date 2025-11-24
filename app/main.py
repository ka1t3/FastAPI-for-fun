# uvicorn main:app --reload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routers import notes
import os
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

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

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middlewares

# Trusted Host Middleware
# Prevents HTTP Host Header attacks. In production, set ALLOWED_HOSTS to your domain.
# "testserver" is required for TestClient
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# CORS Middleware
# Allows cross-origin requests. In production, restrict this to your frontend domain.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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