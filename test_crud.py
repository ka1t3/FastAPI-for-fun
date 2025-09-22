import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ajout du chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, Atom, Molecule, MoleculeAtom, Reaction, ReactionMolecule
from database import get_db

# Configuration de la base de données de test (en mémoire)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fixture pour créer une session de base de données de test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def sample_atoms(db_session):
    """Fixture pour créer des atomes d'exemple"""
    atoms_data = [
        {"symbol": "H", "name": "Hydrogen", "atomic_number": 1, "atomic_mass": 1.008},
        {"symbol": "C", "name": "Carbon", "atomic_number": 6, "atomic_mass": 12.011},
        {"symbol": "O", "name": "Oxygen", "atomic_number": 8, "atomic_mass": 15.999},
        {"symbol": "N", "name": "Nitrogen", "atomic_number": 7, "atomic_mass": 14.007},
    ]

    created_atoms = []
    for atom_data in atoms_data:
        atom = Atom(**atom_data)
        db_session.add(atom)
        created_atoms.append(atom)

    db_session.commit()
    return created_atoms


@pytest.fixture(scope="function")
def sample_molecules(db_session, sample_atoms):
    """Fixture pour créer des molécules d'exemple"""
    molecules_data = [
        {"name": "Water", "formula": "H2O"},
        {"name": "Carbon Dioxide", "formula": "CO2"},
        {"name": "Methane", "formula": "CH4"},
        {"name": "Ammonia", "formula": "NH3"},
    ]

    created_molecules = []
    for molecule_data in molecules_data:
        molecule = Molecule(**molecule_data)
        db_session.add(molecule)
        created_molecules.append(molecule)

    db_session.commit()
    return created_molecules


class TestAtomCRUD:
    """Tests CRUD pour le modèle Atom"""

    def test_create_atom(self, db_session):
        """Test de création d'un atome"""
        initial_count = db_session.query(Atom).count()

        atom = Atom(
            symbol="He",
            name="Helium",
            atomic_number=2,
            atomic_mass=4.003
        )
        db_session.add(atom)
        db_session.commit()

        final_count = db_session.query(Atom).count()
        assert final_count == initial_count + 1

        # Vérification des données
        created_atom = db_session.query(Atom).filter(Atom.symbol == "He").first()
        assert created_atom is not None
        assert created_atom.name == "Helium"
        assert created_atom.atomic_number == 2
        assert created_atom.atomic_mass == 4.003

    def test_read_atoms(self, db_session, sample_atoms):
        """Test de lecture des atomes"""
        atoms = db_session.query(Atom).all()
        assert len(atoms) == 4  # 4 atomes créés dans la fixture

        # Vérification des symboles
        symbols = [atom.symbol for atom in atoms]
        assert "H" in symbols
        assert "C" in symbols
        assert "O" in symbols
        assert "N" in symbols

    def test_read_atom_by_id(self, db_session, sample_atoms):
        """Test de lecture d'un atome par ID"""
        first_atom = sample_atoms[0]
        found_atom = db_session.query(Atom).filter(Atom.atom_id == first_atom.atom_id).first()

        assert found_atom is not None
        assert found_atom.symbol == first_atom.symbol
        assert found_atom.name == first_atom.name

    def test_update_atom(self, db_session, sample_atoms):
        """Test de mise à jour d'un atome"""
        atom_to_update = sample_atoms[0]  # Hydrogen
        original_name = atom_to_update.name

        # Mise à jour
        atom_to_update.name = "Hydrogène"
        db_session.commit()

        # Vérification
        updated_atom = db_session.query(Atom).filter(Atom.atom_id == atom_to_update.atom_id).first()
        assert updated_atom.name == "Hydrogène"
        assert updated_atom.name != original_name

    def test_delete_atom(self, db_session, sample_atoms):
        """Test de suppression d'un atome"""
        initial_count = db_session.query(Atom).count()
        atom_to_delete = sample_atoms[0]

        db_session.delete(atom_to_delete)
        db_session.commit()

        final_count = db_session.query(Atom).count()
        assert final_count == initial_count - 1

        # Vérification que l'atome n'existe plus
        deleted_atom = db_session.query(Atom).filter(Atom.atom_id == atom_to_delete.atom_id).first()
        assert deleted_atom is None


class TestMoleculeCRUD:
    """Tests CRUD pour le modèle Molecule"""

    def test_create_molecule(self, db_session):
        """Test de création d'une molécule"""
        initial_count = db_session.query(Molecule).count()

        molecule = Molecule(name="Ethanol", formula="C2H6O")
        db_session.add(molecule)
        db_session.commit()

        final_count = db_session.query(Molecule).count()
        assert final_count == initial_count + 1

        created_molecule = db_session.query(Molecule).filter(Molecule.name == "Ethanol").first()
        assert created_molecule is not None
        assert created_molecule.formula == "C2H6O"

    def test_read_molecules(self, db_session, sample_molecules):
        """Test de lecture des molécules"""
        molecules = db_session.query(Molecule).all()
        assert len(molecules) == 4  # 4 molécules dans la fixture

        names = [molecule.name for molecule in molecules]
        assert "Water" in names
        assert "Carbon Dioxide" in names
        assert "Methane" in names
        assert "Ammonia" in names

    def test_update_molecule(self, db_session, sample_molecules):
        """Test de mise à jour d'une molécule"""
        molecule_to_update = sample_molecules[0]  # Water
        original_formula = molecule_to_update.formula

        molecule_to_update.formula = "H2O (updated)"
        db_session.commit()

        updated_molecule = db_session.query(Molecule).filter(
            Molecule.molecule_id == molecule_to_update.molecule_id
        ).first()
        assert updated_molecule.formula == "H2O (updated)"
        assert updated_molecule.formula != original_formula

    def test_delete_molecule(self, db_session, sample_molecules):
        """Test de suppression d'une molécule"""
        initial_count = db_session.query(Molecule).count()
        molecule_to_delete = sample_molecules[0]

        db_session.delete(molecule_to_delete)
        db_session.commit()

        final_count = db_session.query(Molecule).count()
        assert final_count == initial_count - 1


class TestMoleculeAtomCRUD:
    """Tests CRUD pour la table de liaison MoleculeAtom"""

    def test_create_molecule_atom_relation(self, db_session, sample_atoms, sample_molecules):
        """Test de création d'une relation molécule-atome"""
        initial_count = db_session.query(MoleculeAtom).count()

        # Water (H2O) = 2 Hydrogen + 1 Oxygen
        water = sample_molecules[0]  # Water
        hydrogen = sample_atoms[0]  # H
        oxygen = sample_atoms[2]  # O

        # 2 atomes d'hydrogène dans l'eau
        molecule_atom_h = MoleculeAtom(
            molecule_id=water.molecule_id,
            atom_id=hydrogen.atom_id,
            atom_count=2
        )

        # 1 atome d'oxygène dans l'eau
        molecule_atom_o = MoleculeAtom(
            molecule_id=water.molecule_id,
            atom_id=oxygen.atom_id,
            atom_count=1
        )

        db_session.add(molecule_atom_h)
        db_session.add(molecule_atom_o)
        db_session.commit()

        final_count = db_session.query(MoleculeAtom).count()
        assert final_count == initial_count + 2

    def test_read_molecule_composition(self, db_session, sample_atoms, sample_molecules):
        """Test de lecture de la composition d'une molécule"""
        # Créer d'abord quelques relations
        water = sample_molecules[0]
        hydrogen = sample_atoms[0]
        oxygen = sample_atoms[2]

        relations = [
            MoleculeAtom(molecule_id=water.molecule_id, atom_id=hydrogen.atom_id, atom_count=2),
            MoleculeAtom(molecule_id=water.molecule_id, atom_id=oxygen.atom_id, atom_count=1)
        ]

        for relation in relations:
            db_session.add(relation)
        db_session.commit()

        # Test de lecture
        composition = db_session.query(MoleculeAtom).filter(
            MoleculeAtom.molecule_id == water.molecule_id
        ).all()

        assert len(composition) == 2

        # Vérification des comptes d'atomes
        atom_counts = {rel.atom_id: rel.atom_count for rel in composition}
        assert atom_counts[hydrogen.atom_id] == 2
        assert atom_counts[oxygen.atom_id] == 1


class TestReactionCRUD:
    """Tests CRUD pour le modèle Reaction"""

    def test_create_reaction(self, db_session):
        """Test de création d'une réaction"""
        initial_count = db_session.query(Reaction).count()

        reaction = Reaction(
            description="Combustion of methane",
            reaction_type="combustion"
        )
        db_session.add(reaction)
        db_session.commit()

        final_count = db_session.query(Reaction).count()
        assert final_count == initial_count + 1

        created_reaction = db_session.query(Reaction).filter(
            Reaction.description == "Combustion of methane"
        ).first()
        assert created_reaction is not None
        assert created_reaction.reaction_type == "combustion"

    def test_read_reactions(self, db_session):
        """Test de lecture des réactions"""
        # Créer quelques réactions de test
        reactions_data = [
            {"description": "Water formation", "reaction_type": "synthesis"},
            {"description": "Salt dissolution", "reaction_type": "dissolution"},
        ]

        for reaction_data in reactions_data:
            reaction = Reaction(**reaction_data)
            db_session.add(reaction)
        db_session.commit()

        reactions = db_session.query(Reaction).all()
        assert len(reactions) == 2

        descriptions = [reaction.description for reaction in reactions]
        assert "Water formation" in descriptions
        assert "Salt dissolution" in descriptions


class TestReactionMoleculeCRUD:
    """Tests CRUD pour la table de liaison ReactionMolecule"""

    def test_create_reaction_molecule_relation(self, db_session, sample_molecules):
        """Test de création d'une relation réaction-molécule"""
        initial_count = db_session.query(ReactionMolecule).count()

        # Créer une réaction
        reaction = Reaction(
            description="Methane combustion",
            reaction_type="combustion"
        )
        db_session.add(reaction)
        db_session.commit()

        # CH4 + 2O2 -> CO2 + 2H2O
        methane = sample_molecules[2]  # CH4
        co2 = sample_molecules[1]  # CO2
        water = sample_molecules[0]  # H2O

        relations = [
            ReactionMolecule(reaction_id=reaction.reaction_id, molecule_id=methane.molecule_id,
                             role="réactif", coefficient=1),
            ReactionMolecule(reaction_id=reaction.reaction_id, molecule_id=co2.molecule_id,
                             role="produit", coefficient=1),
            ReactionMolecule(reaction_id=reaction.reaction_id, molecule_id=water.molecule_id,
                             role="produit", coefficient=2),
        ]

        for relation in relations:
            db_session.add(relation)
        db_session.commit()

        final_count = db_session.query(ReactionMolecule).count()
        assert final_count == initial_count + 3

    def test_read_reaction_participants(self, db_session, sample_molecules):
        """Test de lecture des participants d'une réaction"""
        # Créer une réaction avec des participants
        reaction = Reaction(description="Test reaction", reaction_type="test")
        db_session.add(reaction)
        db_session.commit()

        # Ajouter des participants
        methane = sample_molecules[2]
        co2 = sample_molecules[1]

        relations = [
            ReactionMolecule(reaction_id=reaction.reaction_id, molecule_id=methane.molecule_id,
                             role="réactif", coefficient=1),
            ReactionMolecule(reaction_id=reaction.reaction_id, molecule_id=co2.molecule_id,
                             role="produit", coefficient=1),
        ]

        for relation in relations:
            db_session.add(relation)
        db_session.commit()

        # Test de lecture
        participants = db_session.query(ReactionMolecule).filter(
            ReactionMolecule.reaction_id == reaction.reaction_id
        ).all()

        assert len(participants) == 2

        # Vérification des rôles
        roles = [p.role for p in participants]
        assert "réactif" in roles
        assert "produit" in roles


# Exécution des tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])