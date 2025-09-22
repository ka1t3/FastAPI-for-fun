# Simplified Security Implementation Plan for ChemAPI

## Overview
This plan focuses on adding authentication to your FastAPI chemistry database API while keeping things simple. We'll stick with SQLite and implement read-and-update-only operations with proper security.

## Core Requirements
- ✅ Keep SQLite database
- ✅ Read and Update operations only (no create/delete)
- ✅ Simple authentication system
- ✅ Secure API access
- ✅ Minimal complexity

## 1. Simple Authentication System

### 1.1 API Key Authentication (Simplest Approach)

Since you want simplicity with SQLite, I recommend API key authentication over JWT tokens.

#### Create `security.py`:
```python
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional

# Store API keys in environment or config file
# In production, these should be hashed
VALID_API_KEYS = {
    "chemapi-key-admin-001": {"name": "admin", "role": "admin"},
    "chemapi-key-user-002": {"name": "user1", "role": "user"},
    "chemapi-key-user-003": {"name": "user2", "role": "user"}
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Validate API key from header"""
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    return VALID_API_KEYS[api_key]

async def require_admin(user: dict = Security(get_api_key)):
    """Require admin role for certain operations"""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
```

### 1.2 Alternative: Simple Username/Password with SQLite

If you prefer username/password authentication:

#### Add User table to `models.py`:
```python
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="user")  # "user" or "admin"
    created_at = Column(String(50), default=lambda: datetime.now().isoformat())
```

#### Simple authentication with password:
```python
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str):
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, username: str) -> str:
        # Simple token generation (store in database or cache)
        token = secrets.token_urlsafe(32)
        # Store token with expiration in a simple table
        return token
```

## 2. Secure CORS Configuration

Update `main.py`:
```python
# Replace wildcard CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "PUT"],  # Only allow read and update
    allow_headers=["Content-Type", "X-API-Key"],
)
```

## 3. Read and Update Only Endpoints

### 3.1 Simplified Atom Router

Update `routers/atoms.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Atom
from schemas import Atom as AtomSchema, AtomUpdate
from security import get_api_key, require_admin

router = APIRouter()

# READ endpoints - require any valid API key
@router.get("/atoms", response_model=List[AtomSchema])
async def get_atoms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)  # Require authentication
):
    """Get list of atoms (authenticated users only)"""
    query = db.query(Atom)
    
    if symbol:
        query = query.filter(Atom.symbol == symbol)
    
    atoms = query.offset(skip).limit(limit).all()
    return atoms

@router.get("/atoms/{atom_id}", response_model=AtomSchema)
async def get_atom(
    atom_id: int,
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)  # Require authentication
):
    """Get single atom by ID (authenticated users only)"""
    atom = db.query(Atom).filter(Atom.atom_id == atom_id).first()
    if atom is None:
        raise HTTPException(status_code=404, detail="Atom not found")
    return atom

# UPDATE endpoint - require admin role
@router.put("/atoms/{atom_id}", response_model=AtomSchema)
async def update_atom(
    atom_id: int,
    atom_update: AtomUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)  # Require admin role
):
    """Update atom (admin only)"""
    db_atom = db.query(Atom).filter(Atom.atom_id == atom_id).first()
    if db_atom is None:
        raise HTTPException(status_code=404, detail="Atom not found")
    
    update_data = atom_update.dict(exclude_unset=True)
    
    # Validate unique constraints
    if "symbol" in update_data:
        existing = db.query(Atom).filter(
            Atom.symbol == update_data["symbol"],
            Atom.atom_id != atom_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Symbol already exists")
    
    if "atomic_number" in update_data:
        existing = db.query(Atom).filter(
            Atom.atomic_number == update_data["atomic_number"],
            Atom.atom_id != atom_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Atomic number already exists")
    
    # Apply updates
    for field, value in update_data.items():
        setattr(db_atom, field, value)
    
    db.commit()
    db.refresh(db_atom)
    return db_atom

# Remove DELETE endpoint - not needed
# Remove POST endpoint - not needed
```

### 3.2 Add Similar Routers for Molecules and Reactions

Create `routers/molecules.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Molecule, MoleculeAtom, Atom
from schemas import Molecule as MoleculeSchema, MoleculeUpdate
from security import get_api_key, require_admin

router = APIRouter()

@router.get("/molecules", response_model=List[MoleculeSchema])
async def get_molecules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)
):
    """Get list of molecules (authenticated users only)"""
    query = db.query(Molecule)
    
    if name:
        query = query.filter(Molecule.name.ilike(f"%{name}%"))
    
    molecules = query.offset(skip).limit(limit).all()
    return molecules

@router.get("/molecules/{molecule_id}", response_model=MoleculeSchema)
async def get_molecule(
    molecule_id: int,
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)
):
    """Get single molecule by ID"""
    molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if molecule is None:
        raise HTTPException(status_code=404, detail="Molecule not found")
    return molecule

@router.get("/molecules/{molecule_id}/composition")
async def get_molecule_composition(
    molecule_id: int,
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)
):
    """Get molecule composition (atoms and quantities)"""
    composition = db.query(MoleculeAtom, Atom).join(Atom).filter(
        MoleculeAtom.molecule_id == molecule_id
    ).all()
    
    return [
        {
            "atom": atom.symbol,
            "name": atom.name,
            "count": mol_atom.atom_count
        }
        for mol_atom, atom in composition
    ]

@router.put("/molecules/{molecule_id}", response_model=MoleculeSchema)
async def update_molecule(
    molecule_id: int,
    molecule_update: MoleculeUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Update molecule (admin only)"""
    db_molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if db_molecule is None:
        raise HTTPException(status_code=404, detail="Molecule not found")
    
    update_data = molecule_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_molecule, field, value)
    
    db.commit()
    db.refresh(db_molecule)
    return db_molecule
```

## 4. Rate Limiting (Simple Implementation)

For a simple rate limiter without Redis:

```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
import time

class SimpleRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, key: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > minute_ago]
        
        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

rate_limiter = SimpleRateLimiter(requests_per_minute=60)

async def check_rate_limit(request: Request, api_key: dict = Depends(get_api_key)):
    """Simple rate limiting per API key"""
    key = api_key["name"]
    
    if not rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return api_key
```

## 5. Updated Main Application

Update `main.py`:
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base
from routers import atoms, molecules, reactions
from security import get_api_key

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChemAPI - Secure Chemistry Database API",
    description="Secure API for reading and updating chemistry data",
    version="2.0.0",
    docs_url="/docs",  # Consider disabling in production
    redoc_url="/redoc"
)

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "PUT"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Include routers
app.include_router(atoms.router, prefix="/api/v1", tags=["atoms"])
app.include_router(molecules.router, prefix="/api/v1", tags=["molecules"])
app.include_router(reactions.router, prefix="/api/v1", tags=["reactions"])

@app.get("/")
def read_root():
    """Public endpoint - no authentication required"""
    return {
        "message": "ChemAPI - Secure Chemistry Database API",
        "version": "2.0.0",
        "authentication": "Required - Use X-API-Key header"
    }

@app.get("/health")
def health_check():
    """Public health check"""
    return {"status": "healthy"}

@app.get("/api/v1/stats")
def get_stats(
    db: Session = Depends(get_db),
    api_key: dict = Depends(get_api_key)  # Require authentication
):
    """Database statistics (authenticated users only)"""
    from models import Atom, Molecule, Reaction
    
    return {
        "user": api_key["name"],
        "atoms_count": db.query(Atom).count(),
        "molecules_count": db.query(Molecule).count(),
        "reactions_count": db.query(Reaction).count()
    }
```

## 6. Environment Configuration

Create `.env` file:
```env
# API Keys (in production, store these securely)
API_KEYS=chemapi-key-admin-001,chemapi-key-user-002,chemapi-key-user-003

# CORS Origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Database
DATABASE_URL=sqlite:///./chimie.db
```

Create simple `config.py`:
```python
import os
from typing import List

class Config:
    # API Keys
    API_KEYS: List[str] = os.getenv("API_KEYS", "").split(",")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chimie.db")

config = Config()
```

## 7. Testing the Secured API

### Test with curl:
```bash
# Without API key - should fail
curl http://localhost:8000/api/v1/atoms

# With API key - should work
curl -H "X-API-Key: chemapi-key-user-002" http://localhost:8000/api/v1/atoms

# Update with admin key - should work
curl -X PUT -H "X-API-Key: chemapi-key-admin-001" \
     -H "Content-Type: application/json" \
     -d '{"name": "Hydrogen Updated"}' \
     http://localhost:8000/api/v1/atoms/1

# Update with user key - should fail
curl -X PUT -H "X-API-Key: chemapi-key-user-002" \
     -H "Content-Type: application/json" \
     -d '{"name": "Hydrogen Updated"}' \
     http://localhost:8000/api/v1/atoms/1
```

### Update `test_main.http`:
```http
### Public endpoint - no auth required
GET http://127.0.0.1:8000/
Accept: application/json

###

### Get atoms - requires authentication
GET http://127.0.0.1:8000/api/v1/atoms
Accept: application/json
X-API-Key: chemapi-key-user-002

###

### Update atom - requires admin
PUT http://127.0.0.1:8000/api/v1/atoms/1
Content-Type: application/json
X-API-Key: chemapi-key-admin-001

{
  "name": "Hydrogen Updated"
}

###
```

## 8. Minimal Dependencies Update

Update `requirements.txt`:
```
SQLAlchemy>=2.0.0
pydantic>=2.4.0
fastapi[standard]>=0.115.0
uvicorn>=0.23.0
python-decouple>=3.8
passlib[bcrypt]>=1.7.4
pytest>=8.1.0
httpx>=0.27.0
```

## Implementation Steps

### Step 1: Add Security (30 minutes)
1. Create `security.py` with API key authentication
2. Update `.env` with your API keys
3. Test authentication works

### Step 2: Update Routers (1 hour)
1. Update `routers/atoms.py` to remove POST/DELETE, add authentication
2. Create `routers/molecules.py` with read/update only
3. Create `routers/reactions.py` with read/update only

### Step 3: Update Main App (30 minutes)
1. Update `main.py` with secure CORS
2. Add authentication to protected endpoints
3. Remove any public data endpoints

### Step 4: Test Everything (30 minutes)
1. Test public endpoints work without auth
2. Test protected endpoints require API key
3. Test admin-only updates work correctly
4. Test rate limiting (if implemented)

## Summary

This simplified approach gives you:
- ✅ **Simple API key authentication** (no complex JWT)
- ✅ **Read and Update only** operations
- ✅ **SQLite database** (no changes needed)
- ✅ **Secure CORS** configuration
- ✅ **Role-based access** (users can read, admins can update)
- ✅ **Optional rate limiting** (simple in-memory implementation)
- ✅ **Minimal refactoring** (mostly adding security checks)

Total implementation time: ~2-3 hours

The main changes are:
1. Add authentication checks to all data endpoints
2. Remove POST and DELETE operations
3. Fix CORS to only allow specific origins
4. Add role checking for update operations

This keeps your application simple while adding the essential security you need.