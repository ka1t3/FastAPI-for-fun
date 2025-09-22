from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

# =============================================================================
# 1. CLASSE DE BASE POUR LA CONFIGURATION (évite la répétition)
# =============================================================================

class OrmBaseModel(BaseModel):
    """
    Modèle de base qui configure tous les modèles héritiers pour être
    compatibles avec les objets ORM (comme SQLAlchemy).
    """
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. SCHÉMAS ATOM
# =============================================================================

# --- Tronc commun des champs d'un atome ---
class AtomBase(BaseModel):
    """
    Définit les champs fondamentaux d'un atome.
    Utilisé pour construire le modèle de lecture `Atom`.
    """
    symbol: str = Field(..., max_length=5, description="Chemical symbol (e.g., H, C, O)")
    name: str = Field(..., max_length=100, description="Atom name (e.g., Hydrogen)")
    atomic_number: int = Field(..., gt=0, description="Atomic number")
    atomic_mass: float = Field(..., gt=0, description="Atomic mass")


# --- Schéma pour la MISE À JOUR (UPDATE) ---
class AtomUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un atome.
    Tous les champs sont optionnels pour permettre des mises à jour partielles (PATCH).
    """
    symbol: Optional[str] = Field(None, max_length=5)
    name: Optional[str] = Field(None, max_length=100)
    atomic_number: Optional[int] = Field(None, gt=0)
    atomic_mass: Optional[float] = Field(None, gt=0)


# --- Schéma pour la LECTURE (READ) ---
class Atom(OrmBaseModel, AtomBase):
    """
    Schéma pour renvoyer un atome complet depuis l'API.
    Hérite des champs de AtomBase et de la configuration de OrmBaseModel.
    """
    atom_id: int


# =============================================================================
# 3. SCHÉMAS MOLECULE
# =============================================================================

class MoleculeBase(BaseModel):
    name: str = Field(..., max_length=200, description="Molecule name")
    formula: str = Field(..., max_length=500, description="Chemical formula")

class MoleculeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    formula: Optional[str] = Field(None, max_length=500)


class Molecule(OrmBaseModel,MoleculeBase):
    molecule_id: int


# =============================================================================
# 4. SCHÉMAS MOLECULE_ATOM (composition)
# =============================================================================

class MoleculeAtomBase(BaseModel):
    molecule_id: int
    atom_id: int
    atom_count: int = Field(..., gt=0, description="Number of atoms in the molecule")


class MoleculeAtom(OrmBaseModel, MoleculeAtomBase):
    pass


# =============================================================================
# SCHÉMAS REACTION
# =============================================================================

class ReactionBase(BaseModel):
    description: str = Field(..., description="Reaction description")
    reaction_type: str = Field(..., max_length=100, description="Type of reaction")


class ReactionUpdate(BaseModel):
    description: Optional[str] = None
    reaction_type: Optional[str] = Field(None, max_length=100)


class Reaction(OrmBaseModel, ReactionBase):
    reaction_id: int


# =============================================================================
# SCHÉMAS REACTION_MOLECULE
# =============================================================================

class ReactionMoleculeBase(BaseModel):
    reaction_id: int
    molecule_id: int
    role: str = Field(..., pattern="^(réactif|produit)$", description="Role in reaction")
    coefficient: int = Field(..., gt=0, description="Stoichiometric coefficient")


class ReactionMolecule(OrmBaseModel, ReactionMoleculeBase):
    pass


# =============================================================================
# SCHÉMAS AVEC RELATIONS (pour réponses enrichies)
# =============================================================================

class MoleculeWithAtoms(Molecule):
    """Molécule avec la liste de ses atomes"""
    atoms: List[dict] = []  # Liste des atomes avec leur nombre


class ReactionWithMolecules(Reaction):
    """Réaction avec ses molécules (réactifs et produits)"""
    reactants: List[dict] = []
    products: List[dict] = []