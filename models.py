from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# =============================================================================
# MODÈLES POUR LE DOMAINE CHIMIE (basés sur votre schéma existant)
# =============================================================================

class Atom(Base):
    """Modèle pour les atomes"""
    __tablename__ = "atom"

    atom_id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(5), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    atomic_number = Column(Integer, nullable=False, unique=True)
    atomic_mass = Column(Float, nullable=False)

    # Relations
    molecule_atoms = relationship("MoleculeAtom", back_populates="atom")

    def __repr__(self):
        return f"<Atom(symbol='{self.symbol}', name='{self.name}')>"


class Molecule(Base):
    """Modèle pour les molécules"""
    __tablename__ = "molecule"

    molecule_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    formula = Column(String(500), nullable=False)

    # Relations
    molecule_atoms = relationship("MoleculeAtom", back_populates="molecule")
    reaction_molecules = relationship("ReactionMolecule", back_populates="molecule")

    def __repr__(self):
        return f"<Molecule(name='{self.name}', formula='{self.formula}')>"


class MoleculeAtom(Base):
    """Table de liaison entre molécules et atomes"""
    __tablename__ = "molecule_atom"

    molecule_id = Column(Integer, ForeignKey("molecule.molecule_id"), primary_key=True)
    atom_id = Column(Integer, ForeignKey("atom.atom_id"), primary_key=True)
    atom_count = Column(Integer, nullable=False)

    # Relations
    molecule = relationship("Molecule", back_populates="molecule_atoms")
    atom = relationship("Atom", back_populates="molecule_atoms")

    def __repr__(self):
        return f"<MoleculeAtom(molecule_id={self.molecule_id}, atom_id={self.atom_id}, count={self.atom_count})>"


class Reaction(Base):
    """Modèle pour les réactions chimiques"""
    __tablename__ = "reaction"

    reaction_id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    reaction_type = Column(String(100), nullable=False, index=True)

    # Relations
    reaction_molecules = relationship("ReactionMolecule", back_populates="reaction")

    def __repr__(self):
        return f"<Reaction(id={self.reaction_id}, type='{self.reaction_type}')>"


class ReactionMolecule(Base):
    """Table de liaison entre réactions et molécules"""
    __tablename__ = "reaction_molecule"

    reaction_id = Column(Integer, ForeignKey("reaction.reaction_id"), primary_key=True)
    molecule_id = Column(Integer, ForeignKey("molecule.molecule_id"), primary_key=True)
    role = Column(String(20), nullable=False, primary_key=True)
    coefficient = Column(Integer, nullable=False)

    # Contrainte pour s'assurer que role est soit 'réactif' soit 'produit'
    __table_args__ = (
        CheckConstraint("role IN ('réactif', 'produit')", name="check_role"),
    )

    # Relations
    reaction = relationship("Reaction", back_populates="reaction_molecules")
    molecule = relationship("Molecule", back_populates="reaction_molecules")

    def __repr__(self):
        return f"<ReactionMolecule(reaction_id={self.reaction_id}, molecule_id={self.molecule_id}, role='{self.role}')>"

