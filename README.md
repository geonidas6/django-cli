# 📚 Django CLI Tools & Documentation

Bienvenue dans ce projet Django (**GestEcole**). Ce dépôt contient des outils en ligne de commande pour accélérer le développement, ainsi que des guides essentiels pour la gestion et le déploiement.

## 🛠️ Outils CLI

Ce projet inclut deux scripts Python puissants pour automatiser les tâches répétitives :

### 1. [django-cli.py](django-cli.py) - Générateur CRUD
Un outil similaire à `artisan` ou `symfony console` pour générer du code rapidement.
*   **Création d'Apps** : `make:app`
*   **Génération de Modèles** : `make:model` (Interactif)
*   **CRUD Complet** : `make:crud` (Génère Views, URLs, Forms, Templates)
*   **Listing des routes** : `route:list`

👉 **[Voir le Tutoriel Complet du CLI](TUTORIAL_DJANGO_CLI.md)**

### 2. [django-auth-cli.py](django-auth-cli.py) - Système d'Authentification
Un script pour initialiser un système d'authentification complet et robuste en une seule commande.
*   Gère les utilisateurs personnalisés (`CustomUser` avec photo).
*   Crée les groupes et rôles (`Admin`, `Manager`, `Membre`).
*   Génère les vues de connexion, inscription, et un dashboard moderne.

---

## 📖 Documentation

Voici les guides disponibles pour vous aider à chaque étape du projet :

### 🚀 [Guide de Déploiement (DEPLOY.md)](DEPLOY.md)
*   Configuration de **Gunicorn** & **Nginx**.
*   Sécurisation avec **SSL (Certbot)**.
*   Gestion des fichiers statiques et settings de production.

### 💡 [Commandes Utiles (util.md)](util.md)
*   Aide-mémoire pour les commandes courantes (startproject, runserver, migrations).
*   Initialisation d'un environnement virtuel.

### 📘 [Tutoriel Django CLI (TUTORIAL_DJANGO_CLI.md)](TUTORIAL_DJANGO_CLI.md)
*   Documentation détaillée pour utiliser `django-cli.py` et `django-auth-cli.py`.

---

## ⚡ Démarrage Rapide

1.  **Installez les dépendances** :
    ```bash
    pip install django pillow
    ```
2.  **Lancez le serveur** :
    ```bash
    python manage.py runserver
    ```
3.  **Utilisez le CLI** :
    ```bash
    python django-cli.py route:list
    ```
