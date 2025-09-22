"""
Reactions router with authentication
Read and Update operations only (no Create or Delete)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from database import get_db
from models import Reaction, ReactionMolecule, Molecule
from schemas import Reaction as ReactionSchema, ReactionUpdate
from security import require_user, require_admin

router = APIRouter()


@router.get("/reactions", response_model=List[ReactionSchema])
async def get_reactions(
    skip: int = Query(0, ge=0, description="Number of reactions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of reactions to return"),
    reaction_type: Optional[str] = Query(None, description="Filter by reaction type"),
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get list of reactions (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    query = db.query(Reaction)
    
    if reaction_type:
        query = query.filter(Reaction.reaction_type.ilike(f"%{reaction_type.replace('%', '%%')}%"))
    
    reactions = query.offset(skip).limit(limit).all()
    return reactions


@router.get("/reactions/{reaction_id}", response_model=ReactionSchema)
async def get_reaction(
    reaction_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get single reaction by ID (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    reaction = db.query(Reaction).filter(Reaction.reaction_id == reaction_id).first()
    if reaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reaction with id {reaction_id} not found"
        )
    return reaction


@router.get("/reactions/{reaction_id}/participants")
async def get_reaction_participants(
    reaction_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get reaction participants - reactants and products (authenticated users only)
    
    Returns the molecules involved in this reaction, separated by role.
    
    Requires: Valid API key (user or admin)
    """
    # Check if reaction exists
    reaction = db.query(Reaction).filter(Reaction.reaction_id == reaction_id).first()
    if reaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reaction with id {reaction_id} not found"
        )
    
    # Get all participants
    participants = db.query(ReactionMolecule, Molecule).join(
        Molecule, ReactionMolecule.molecule_id == Molecule.molecule_id
    ).filter(
        ReactionMolecule.reaction_id == reaction_id
    ).all()
    
    # Separate reactants and products
    reactants = []
    products = []
    
    for reaction_mol, molecule in participants:
        participant_data = {
            "molecule_id": molecule.molecule_id,
            "name": molecule.name,
            "formula": molecule.formula,
            "coefficient": reaction_mol.coefficient
        }
        
        if reaction_mol.role == "réactif":
            reactants.append(participant_data)
        elif reaction_mol.role == "produit":
            products.append(participant_data)
    
    # Format response
    result = {
        "reaction_id": reaction_id,
        "description": reaction.description,
        "reaction_type": reaction.reaction_type,
        "reactants": reactants,
        "products": products,
        "equation": _format_equation(reactants, products)
    }
    
    return result


def _format_equation(reactants: List[Dict], products: List[Dict]) -> str:
    """Helper function to format chemical equation"""
    reactant_parts = []
    for r in reactants:
        coef = "" if r["coefficient"] == 1 else str(r["coefficient"])
        reactant_parts.append(f"{coef}{r['formula']}")
    
    product_parts = []
    for p in products:
        coef = "" if p["coefficient"] == 1 else str(p["coefficient"])
        product_parts.append(f"{coef}{p['formula']}")
    
    return f"{' + '.join(reactant_parts)} → {' + '.join(product_parts)}"


@router.put("/reactions/{reaction_id}", response_model=ReactionSchema)
async def update_reaction(
    reaction_id: int,
    reaction_update: ReactionUpdate,
    db: Session = Depends(get_db),
    current_admin: Dict[str, str] = Depends(require_admin)  # Admin only
):
    """
    Update reaction (admin only)
    
    Only updates the reaction's description and type.
    To update participants, use a separate endpoint (if implemented).
    
    Requires: Valid API key with admin role
    """
    # Find the reaction
    db_reaction = db.query(Reaction).filter(Reaction.reaction_id == reaction_id).first()
    if db_reaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reaction with id {reaction_id} not found"
        )
    
    # Get update data (exclude unset fields for partial updates)
    update_data = reaction_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(db_reaction, field, value)
    
    try:
        db.commit()
        db.refresh(db_reaction)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reaction"
        )
    
    return db_reaction


@router.get("/reactions/search/by-molecule/{molecule_id}")
async def search_reactions_by_molecule(
    molecule_id: int,
    role: Optional[str] = Query(None, regex="^(réactif|produit)$", description="Filter by role"),
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Search reactions involving a specific molecule (authenticated users only)
    
    Optionally filter by the molecule's role (réactif or produit).
    
    Requires: Valid API key (user or admin)
    """
    # Check if molecule exists
    molecule = db.query(Molecule).filter(Molecule.molecule_id == molecule_id).first()
    if molecule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Molecule with id {molecule_id} not found"
        )
    
    # Build query
    query = db.query(Reaction, ReactionMolecule).join(
        ReactionMolecule, Reaction.reaction_id == ReactionMolecule.reaction_id
    ).filter(
        ReactionMolecule.molecule_id == molecule_id
    )
    
    # Apply role filter if specified
    if role:
        query = query.filter(ReactionMolecule.role == role)
    
    results = query.all()
    
    # Format response
    reactions_data = []
    for reaction, reaction_mol in results:
        reactions_data.append({
            "reaction_id": reaction.reaction_id,
            "description": reaction.description,
            "reaction_type": reaction.reaction_type,
            "molecule_role": reaction_mol.role,
            "coefficient": reaction_mol.coefficient
        })
    
    return {
        "molecule": {
            "molecule_id": molecule.molecule_id,
            "name": molecule.name,
            "formula": molecule.formula
        },
        "reactions": reactions_data,
        "count": len(reactions_data)
    }


@router.get("/reactions/types")
async def get_reaction_types(
    db: Session = Depends(get_db),
    current_user: Dict[str, str] = Depends(require_user)  # Authentication required
):
    """
    Get all unique reaction types in the database (authenticated users only)
    
    Requires: Valid API key (user or admin)
    """
    types = db.query(Reaction.reaction_type).distinct().all()
    return {
        "reaction_types": [t[0] for t in types if t[0]],
        "count": len(types)
    }


# Note: DELETE endpoint not implemented - not needed for read/update only API
# Note: POST endpoint not implemented - not needed for read/update only API
# Note: Participant update endpoints not implemented - can be added if needed