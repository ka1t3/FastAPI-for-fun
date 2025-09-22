import csv
import sqlite3
import os

# --- Configuration ---
NOM_BASE_DE_DONNEES = 'chimie.db'

# Dictionnaire décrivant les fichiers CSV, les noms de table et leurs colonnes
CONFIG_TABLES = {
    'atom': {
        'fichier': 'atom.csv',
        'colonnes': ['atom_id', 'symbol', 'name', 'atomic_number', 'atomic_mass']
    },
    'molecule': {
        'fichier': 'molecule.csv',
        'colonnes': ['molecule_id', 'name', 'formula']
    },
    'molecule_atom': {
        'fichier': 'molecule_atom.csv',
        'colonnes': ['molecule_id', 'atom_id', 'atom_count']
    },
    'reaction': {
        'fichier': 'reaction.csv',
        'colonnes': ['reaction_id', 'description', 'reaction_type']
    },
    'reaction_molecule': {
        'fichier': 'reaction_molecule.csv',
        'colonnes': ['reaction_id', 'molecule_id', 'role', 'coefficient']
    }
}

# --- Création de la base de données et des tables ---

# Supprimer l'ancienne base de données si elle existe pour un nouveau départ propre
if os.path.exists(NOM_BASE_DE_DONNEES):
    os.remove(NOM_BASE_DE_DONNEES)

# Connexion à la base de données (le fichier sera créé)
conn = sqlite3.connect(NOM_BASE_DE_DONNEES)
cursor = conn.cursor()

print("Création des tables...")

# Création de la table 'atom'
cursor.execute("""
               CREATE TABLE IF NOT EXISTS atom
               (
                   atom_id INTEGER PRIMARY KEY,
                   symbol TEXT NOT NULL,
                   name TEXT NOT NULL,
                   atomic_number INTEGER NOT NULL,
                   atomic_mass REAL NOT NULL
               )
               """)

# Création de la table 'molecule'
cursor.execute("""
               CREATE TABLE IF NOT EXISTS molecule
               (
                   molecule_id INTEGER PRIMARY KEY,
                   name TEXT NOT NULL,
                   formula TEXT NOT NULL
               )
               """)

# Création de la table de liaison 'molecule_atom'
cursor.execute("""

                CREATE TABLE IF NOT EXISTS molecule_atom (
                    molecule_id INTEGER,
                    atom_id INTEGER,
                    atom_count INTEGER NOT NULL,
                    PRIMARY KEY (molecule_id, atom_id),
                    FOREIGN KEY (molecule_id) REFERENCES molecule(molecule_id),
                    FOREIGN KEY (atom_id) REFERENCES atom(atom_id)
)
""")

# Création de la table 'reaction'
cursor.execute("""
CREATE TABLE IF NOT EXISTS reaction (
    reaction_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    reaction_type TEXT NOT NULL
)
""")

# Création de la table de liaison 'reaction_molecule'
cursor.execute("""
CREATE TABLE IF NOT EXISTS reaction_molecule (
    reaction_id INTEGER,
    molecule_id INTEGER,
    role TEXT NOT NULL CHECK(role IN ('réactif', 'produit')),
    coefficient INTEGER NOT NULL,
    PRIMARY KEY (reaction_id, molecule_id, role),
    FOREIGN KEY (reaction_id) REFERENCES reaction(reaction_id),
    FOREIGN KEY (molecule_id) REFERENCES molecule(molecule_id)
)
""")

print("Tables créées avec succès.")


# --- Importation des données depuis les fichiers CSV ---

def importer_csv(nom_table, info_table):
    """Importe les données d'un fichier CSV dans une table de la base de données."""
    nom_fichier_csv = info_table['fichier']
    colonnes = info_table['colonnes']

    try:
        with open(nom_fichier_csv, 'r', newline='', encoding='utf-8') as fichier:
            lecteur_csv = csv.reader(fichier)
            next(lecteur_csv)  # Ignorer l'en-tête

            # Préparer la requête d'insertion
            placeholders = ', '.join(['?'] * len(colonnes))
            requete_insertion = f"INSERT INTO {nom_table} ({', '.join(colonnes)}) VALUES ({placeholders})"

            # Utiliser executemany pour une insertion efficace
            cursor.executemany(requete_insertion, lecteur_csv)
            print(f"-> Données de '{nom_fichier_csv}' importées dans la table '{nom_table}'.")

    except FileNotFoundError:
        print(f"ERREUR: Le fichier '{nom_fichier_csv}' est introuvable. Veuillez vérifier son emplacement.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'importation de '{nom_fichier_csv}': {e}")


# Itérer sur la configuration pour importer chaque fichier
for nom_table, info in CONFIG_TABLES.items():
    importer_csv(nom_table, info)

# --- Finalisation ---
conn.commit()
conn.close()

print(f"\nL'opération est terminée. La base de données '{NOM_BASE_DE_DONNEES}' a été créée et remplie.")

