"""
Atoms router with authentication
Read and Update operations only (no Create or Delete)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from database import get_db
from models import Atom
from schemas import Atom as AtomSchema, AtomUpdate
from security import require_user, require_admin

router = APIRouter()


@router.get("/atoms", response_model=List[AtomSchema])
async def get_atoms(
    skip: int = Query(0, ge=0, description="Number of atoms to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of atoms to return"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get list of atoms (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    query = db.query(Atom)

    if symbol:
        # Exact match for symbol (case-insensitive)
        query = query.filter(Atom.symbol.ilike(f"%{symbol.replace('%', '%%')}%"))

    atoms = query.offset(skip).limit(limit).all()
    return atoms


@router.get("/atoms/{atom_id}", response_model=AtomSchema)
async def get_atom(
    atom_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get single atom by ID (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    atom = db.query(Atom).filter(Atom.atom_id == atom_id).first()
    if atom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atom with id {atom_id} not found"
        )
    return atom


@router.put("/atoms/{atom_id}", response_model=AtomSchema)
async def update_atom(
    atom_id: int,
    atom_update: AtomUpdate,
    db: Session = Depends(get_db),
    current_admin: Dict[str, str] = Depends(require_admin)  # Admin only
):
    """
    Update atom (admin only)
    
    Requires: Valid API key with admin role
    """
    # Find the atom
    db_atom = db.query(Atom).filter(Atom.atom_id == atom_id).first()
    if db_atom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atom with id {atom_id} not found"
        )

    # Get update data (exclude unset fields for partial updates)
    update_data = atom_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Check unique constraints
    if "symbol" in update_data:
        existing = db.query(Atom).filter(
            Atom.symbol == update_data["symbol"],
            Atom.atom_id != atom_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Symbol '{update_data['symbol']}' already exists"
            )

    if "atomic_number" in update_data:
        existing = db.query(Atom).filter(
            Atom.atomic_number == update_data["atomic_number"],
            Atom.atom_id != atom_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Atomic number {update_data['atomic_number']} already exists"
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(db_atom, field, value)

    try:
        db.commit()
        db.refresh(db_atom)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update atom"
        )

    return db_atom


# Note: DELETE endpoint removed - not needed for read/update only API
# Note: POST endpoint removed - not needed for read/update only API