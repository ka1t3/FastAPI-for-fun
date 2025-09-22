"""
ChemAPI - Secure Chemistry Database API
Read and Update operations only with API key authentication
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base
from routers import atoms, molecules, reactions
from security import require_user
from decouple import config
import uvicorn

# Création des tables au démarrage
Base.metadata.create_all(bind=engine)

# Load allowed origins from environment
ALLOWED_ORIGINS = config('ALLOWED_ORIGINS', default='http://localhost:3000').split(',')

app = FastAPI(
    title="ChemAPI - Secure Chemistry Database API",
    description="Secure API for reading and updating chemistry data: atoms, molecules, and reactions. Requires API key authentication.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Secure CORS configuration - only allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "PUT"],  # Only read and update operations
    allow_headers=["Content-Type", "X-API-Key"],  # Only necessary headers
)

# Include routers with authentication
app.include_router(atoms.router, prefix="/api/v1", tags=["atoms"])
app.include_router(molecules.router, prefix="/api/v1", tags=["molecules"])
app.include_router(reactions.router, prefix="/api/v1", tags=["reactions"])


@app.get("/")
async def read_root():
    """Public endpoint - no authentication required"""
    return {
        "message": "Welcome to ChemAPI - Secure Chemistry Database API",
        "version": "2.0.0",
        "authentication": "Required for data access - Use X-API-Key header",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "public": ["/", "/health"],
            "authenticated": ["/api/v1/*"],
            "admin_only": ["/api/v1/*/ (PUT operations)"]
        }
    }


@app.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChemAPI",
        "version": "2.0.0"
    }


@app.get("/api/v1/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_user)  # Authentication required
):
    """Database statistics (authenticated users only)"""
    from models import Atom, Molecule, Reaction

    return {
        "user": current_user["name"],
        "role": current_user["role"],
        "atoms_count": db.query(Atom).count(),
        "molecules_count": db.query(Molecule).count(),
        "reactions_count": db.query(Reaction).count(),
        "api_version": "2.0.0"
    }


@app.get("/api/v1/auth-test")
async def auth_test(current_user: dict = Depends(require_user)):
    """Test endpoint to verify authentication works"""
    return {
        "authenticated": True,
        "user": current_user["name"],
        "role": current_user["role"],
        "message": "Authentication successful"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)