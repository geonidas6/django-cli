# Tutoriel d'utilisation : Générateur CRUD Django (django-cli.py)

Ce script vous permet de générer des applications, des modèles et des CRUD complets via la ligne de commande, similaire à Symfony ou Laravel.

## Commandes Disponibles

### 1. Créer une nouvelle Application
Crée une application Django standard et l'enregistre automatiquement dans `settings.py`.
```bash
python django-cli.py make:app <nom_app>
```
*Exemple : `python django-cli.py make:app professeur`*

### 2. Créer un Modèle (Interactif)
Crée un modèle dans l'application spécifiée. Le script vous demandera **interactivement** de définir les champs.
```bash
python django-cli.py make:model <nom_app> <nom_modele>
```
**Fonctionnalités avancées :**
*   **Modification de modèle existant** : Si le modèle existe déjà, le script vous demandera si vous voulez ajouter de nouveaux champs.
*   **Relations** : Vous pouvez choisir des types de champs `foreignkey`, `onetoone` ou `manytomany`. Le script vous demandera le modèle lié (ex: `eleve.Student` ou `auth.User`).

*Exemple d'interaction :*
```text
> New property name (or press <Enter> to stop): user
  Field types: string... Relations: foreignkey, onetoone, manytomany
  > Field type [string]: foreignkey
  > Related Model: auth.User
  > Can this field be null...? [no]: no
  ✓ Added field 'user'
```

### 3. Générer un CRUD Complet
Génère Forms, Views, URLs et Templates pour un modèle donné.
```bash
python django-cli.py make:crud <nom_app> <nom_modele>
```
**Note importante** : Si le modèle n'existe pas ou si vous souhaitez le modifier, cette commande lancera l'interface interactive de modèle avant de générer le CRUD.

### Autres commandes unitaires
*   `python django-cli.py make:form <app> <model>` : Génère seulement `forms.py`.
*   `python django-cli.py make:view <app> <model>` : Génère `views.py`, `urls.py` et les templates.
*   `python django-cli.py route:list` : Liste toutes les routes (URLs) enregistrées dans le projet.

## Système d'Authentification & Rôles
Vous pouvez générer un système d'authentification complet (Custom User, Rôles, Dashboard) en utilisant :
```bash
python django-auth-cli.py
```
**Ce que cela fait :**
*   **Modèle Utilisateur Personnalisé** : Création d'un `CustomUser` avec champ `photo_profil`.
*   **Rôles (Groupes)** : Création automatique de `Admin_Site`, `Manager` et `Membre`.
*   **Dashboard** : Dashboard unifié basé sur les rôles.
*   **Page d'Accueil (Landing Page)** : Optionnelle, à la racine `/`, ou redirection directe vers le dashboard.
*   **Sécurité Admin** : Possibilité de personnaliser l'URL d'administration (ex: `/secret-admin/` au lieu de `/admin/`).
*   **Deep Clean** : Réinitialisation sécurisée de l'environnement en cas de conflit de migration.
*   **Comptes de Test** : Génération automatique des comptes `superuser` et `admin`.
*   **Signaux** : Assignation automatique d'un groupe aux nouveaux inscrits.
*   **Interactivité** : Options pour activer la Double Auth (2FA) et l'Email de bienvenue.

## Workflow Typique

1.  **Générer le CRUD (et le modèle en même temps)** :
    ```bash
    python django-cli.py make:crud boutique Produit
    ```
    *Suivez les instructions pour ajouter des champs comme `prix` (float), `categorie` (foreignkey).*

2.  **Faire les migrations** :
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

3.  **Finaliser le wiring** :
    Assurez-vous que `boutique/urls.py` est inclus dans le `urls.py` principal du projet.
