"""
Molecules router with authentication
Read and Update operations only (no Create or Delete)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from database import get_db
from models import Molecule, MoleculeAtom, Atom
from schemas import Molecule as MoleculeSchema, MoleculeUpdate
from security import require_user, require_admin

router = APIRouter()


@router.get("/molecules", response_model=List[MoleculeSchema])
async def get_molecules(
    skip: int = Query(0, ge=0, description="Number of molecules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of molecules to return"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    formula: Optional[str] = Query(None, description="Filter by formula"),
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get list of molecules (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    query = db.query(Molecule)
    
    if name:
        query = query.filter(Molecule.name.ilike(f"%{name.replace('%', '%%')}%"))
    
    if formula:
        query = query.filter(Molecule.formula.ilike(f"%{formula.replace('%', '%%')}%"))
    
    molecules = query.offset(skip).limit(limit).all()
    return molecules


@router.get("/molecules/{molecule_id}", response_model=MoleculeSchema)
async def get_molecule(
    molecule_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get single molecule by ID (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if molecule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Molecule with id {molecule_id} not found"
        )
    return molecule


@router.get("/molecules/{molecule_id}/composition")
async def get_molecule_composition(
    molecule_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get molecule composition - atoms and their quantities (authenticated users only)
    
    Returns the atoms that compose this molecule and their counts.
    
    Requires: Valid API key (user or admin)
    """
    # Check if molecule exists
    molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if molecule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Molecule with id {molecule_id} not found"
        )
    
    # Get composition
    composition = db.query(MoleculeAtom, Atom).join(
        Atom, MoleculeAtom.atom_id == Atom.atom_id
    ).filter(
        MoleculeAtom.molecule_id == molecule_id
    ).all()
    
    # Format response
    result = {
        "molecule_id": molecule_id,
        "molecule_name": molecule.name,
        "formula": molecule.formula,
        "composition": [
            {
                "atom_id": atom.atom_id,
                "symbol": atom.symbol,
                "name": atom.name,
                "count": mol_atom.atom_count
            }
            for mol_atom, atom in composition
        ]
    }
    
    return result


@router.put("/molecules/{molecule_id}", response_model=MoleculeSchema)
async def update_molecule(
    molecule_id: int,
    molecule_update: MoleculeUpdate,
    db: Session = Depends(get_db),
    current_admin: Dict[str, str] = Depends(require_admin)  # Admin only
):
    """
    Update molecule (admin only)
    
    Only updates the molecule's name and formula.
    To update composition, use a separate endpoint (if implemented).
    
    Requires: Valid API key with admin role
    """
    # Find the molecule
    db_molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if db_molecule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Molecule with id {molecule_id} not found"
        )
    
    # Get update data (exclude unset fields for partial updates)
    update_data = molecule_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(db_molecule, field, value)
    
    try:
        db.commit()
        db.refresh(db_molecule)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update molecule"
        )
    
    return db_molecule


@router.get("/molecules/search/by-atom/{atom_symbol}")
async def search_molecules_by_atom(
    atom_symbol: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Search molecules containing a specific atom (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    # Find the atom
    atom = db.query(Atom).filter(Atom.symbol.ilike(atom_symbol.replace('%', '%%'))).first()
    if atom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atom with symbol '{atom_symbol}' not found"
        )
    
    # Find molecules containing this atom
    molecules = db.query(Molecule).join(
        MoleculeAtom, Molecule.molecule_id == MoleculeAtom.molecule_id
    ).filter(
        MoleculeAtom.atom_id == atom.atom_id
    ).all()
    
    return {
        "atom": {
            "symbol": atom.symbol,
            "name": atom.name
        },
        "molecules": [
            {
                "molecule_id": mol.molecule_id,
                "name": mol.name,
                "formula": mol.formula
            }
            for mol in molecules
        ],
        "count": len(molecules)
    }


# Note: DELETE endpoint not implemented - not needed for read/update only API
# Note: POST endpoint not implemented - not needed for read/update only API
# Note: Composition update endpoints not implemented - can be added if needed