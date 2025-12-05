# Calculateur de Facteurs d'Échelle (TRAE)

Ce projet est une application Python utilisant **Streamlit** pour calculer les facteurs d'échelle (Grid, Height, Combined) à partir de coordonnées WGS84, UTM ou de fichiers par lot.

## Prérequis

1.  **Python 3.8+** doit être installé sur votre machine.
2.  (Optionnel mais recommandé) Avoir `git` si vous clonez le dépôt.

## Installation et Lancement Rapide

Vous pouvez utiliser le script PowerShell ou les commandes manuelles ci-dessous.

### Option 1 : Via Terminal (Recommandé)

Ouvrez un terminal (PowerShell ou CMD) dans le dossier du projet et exécutez les commandes suivantes :

1.  **Créer un environnement virtuel** (à faire une seule fois) :
    ```powershell
    python -m venv .venv
    ```

2.  **Activer l'environnement virtuel** :
    ```powershell
    # Windows PowerShell
    .venv\Scripts\Activate
    ```
    *(Vous verrez `(.venv)` apparaître au début de la ligne de commande)*.

3.  **Installer les dépendances** :
    ```powershell
    pip install -r requirements.txt
    ```

4.  **Lancer l'application** :
    ```powershell
    streamlit run app.py
    ```

L'application s'ouvrira automatiquement dans votre navigateur par défaut (généralement à l'adresse `http://localhost:8501`).

## Utilisation

### 1. Point WGS84
- Entrez la Latitude et Longitude (Format DMS ou Degrés Décimaux).
- Entrez la hauteur ellipsoïdale.
- Cliquez sur **Calculer**.

### 2. Point UTM
- Entrez le Fuseau, X, Y et la hauteur.
- Cliquez sur **Calculer**.

### 3. Import Fichier (Batch)
- Chargez un fichier **CSV** ou **Excel**.
- Format typique : `ID, X, Y, Z` (les noms de colonnes sont configurables).
- Cliquez sur **Lancer le traitement**.
- Téléchargez le fichier de résultats au format CSV.

## Structure du Projet

- `app.py` : Code principal de l'interface graphique.
- `calc_logic.py` : Logique mathématique des calculs géodésiques.
- `requirements.txt` : Liste des librairies nécessaires.
