# 📚 Django CLI Tools

Bienvenue dans le projet **GestEcole**. Ce dépôt met à disposition des outils en ligne de commande pour simplifier la création et la gestion d'applications Django.

## 🚀 Installation & Démarrage

Suivez ces étapes pour installer et lancer le projet rapidement.

### 1. Cloner le projet
Récupérez le code source depuis GitHub :

```bash
git clone https://github.com/geonidas6/django-cli.git
cd django-cli
```

### 2. Créer un Environnement Virtuel
Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances :
```bash
python -m venv .venv
```

Activez l'environnement :
*   **Mac/Linux** : `source .venv/bin/activate`
*   **Windows** : `.venv\Scripts\activate`

### 3. Installer les Dépendances
Installez Django et les bibliothèques requises (comme Pillow pour les images) :
```bash
pip install django pillow
```

### 4. Initialiser le Projet
Ce dépôt fournit les outils mais pas le projet Django de base. Initialisez-le :
```bash
# Crée le projet dans le dossier courant
# IMPORTANT : Utilisez le nom 'gest_ecole' car les scripts CLI sont pré-configurés pour ce nom.
# Si vous choisissez un autre nom, vous devrez modifier la variable PROJECT_NAME dans les scripts.
django-admin startproject gest_ecole .
```

### 5. Lancer le Projet
Une fois le projet initialisé :
```bash
python manage.py runserver
```
L'application sera accessible sur [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🛠️ Utilisation des Outils CLI

Ce projet fournit deux scripts principaux pour accélérer votre développement :

### 🔹 [django-cli.py](TUTORIAL_DJANGO_CLI.md) (Générateur CRUD)
Générez automatiquement des applications, modèles, vues, formulaires et templates.
```bash
# Exemple : Créer un CRUD complet pour un modèle 'Produit' dans l'app 'boutique'
python django-cli.py make:crud boutique Produit
```
👉 **[Voir le Tutoriel Complet](TUTORIAL_DJANGO_CLI.md)**

### 🔹 [django-auth-cli.py](TUTORIAL_DJANGO_CLI.md#système-dauthentification--rôles) (Auth System)
Installez un système d'authentification complet (Login, Register, Dashboard, Rôles) en une commande :
```bash
python django-auth-cli.py
```

---

## 📖 Documentation & Ressources

*   **[📝 Tutoriel & Guide des Commandes (TUTORIAL_DJANGO_CLI.md)](TUTORIAL_DJANGO_CLI.md)** : Documentation détaillée des scripts.
*   **[💡 Cheat Sheet (CHEATSHEET.md)](CHEATSHEET.md)** : Aide-mémoire des commandes Django essentielles.
*   **[🚀 Guide de Déploiement (DEPLOY.md)](DEPLOY.md)** : Mettre le site en ligne (Gunicorn, Nginx, SSL).

---

## 🤝 Contribuer
Les Pull Requests sont les bienvenues ! Pour des changements majeurs, merci d'ouvrir une issue pour discuter de ce que vous souhaitez changer.
