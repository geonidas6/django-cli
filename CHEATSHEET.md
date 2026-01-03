# 🛠️ Commandes Essentielles Django

Voici les commandes de base pour démarrer et gérer un projet Django.

[🚀 Voir le Guide de Déploiement en Production (DEPLOY.md)](DEPLOY.md)

---

## 0️⃣ Initialisation d'un Projet (De zéro)

1.  **Créer un dossier pour le projet** :
    ```bash
    mkdir mon_projet
    cd mon_projet
    ```

2.  **Créer un environnement virtuel (.venv)** :
    Cela permet d'isoler les dépendances du projet.
    ```bash
    python -m venv .venv
    ```

3.  **Activer l'environnement virtuel** :
    *   **Mac/Linux** : `source .venv/bin/activate`
    *   **Windows** : `.venv\Scripts\activate`

4.  **Installer Django** :
    ```bash
    pip install django
    ```

5.  **Démarrer le projet Django** :
    ```bash
    # Crée le projet dans le dossier courant (avec le nom du dossier)
    python django-cli.py init:project
    ```
    *(Plus besoin de deviner le nom du projet !)*

---

## 1️⃣ Démarrer l'application (Runserver)

Pour tester ton application en local :

1.  Assure-toi que ton venv est actif (`source .venv/bin/activate`).
2.  Lance la commande :
    ```bash
    python manage.py runserver
    ```
    *   Accesible sur : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 2️⃣ Gestion de la Base de Données (Migrations)

Dès que tu modifies `models.py`, tu dois :

1.  **Créer les fichiers de migration** :
    ```bash
    python manage.py makemigrations
    ```
2.  **Appliquer les changements** à la base de données :
    ```bash
    python manage.py migrate
    ```

---

## 3️⃣ Créer un Super Utilisateur (Admin)

Pour accéder à l'interface d'administration `/admin/` :

```bash
python manage.py createsuperuser
```
(Suis les instructions pour email et mot de passe).

---

## 4️⃣ Générateur CRUD Interactif (CLI)

Pour générer rapidement tout le système d'authentification et d'administration (Vues, URLs, Templates, Forms) :

```bash
python django-auth-cli.py
```
*   Ce script va créer/écraser l'application `accounts` avec les dernières fonctionnalités (Navbar horizontale, Gestion Utilisateurs, Groupes, Profil, etc.).

---

## 5️⃣ Astuces Utiles

*   **Voir la version de Django** : `python -m django --version`
*   **Lancer sur tout le réseau local** : `python manage.py runserver 0.0.0.0:8000`
*   **Collecter les fichiers statiques** (Production) : `python manage.py collectstatic`

---
[En savoir plus sur la mise en production](DEPLOY.md)
