# 🚀 Guide de Déploiement en Production (Django)

Ce guide détaille les étapes pour mettre en production votre projet **GestEcole**.

## 1. Pré-requis Serveur

*   Un serveur VPS (Ubuntu 22.04/24.04 recommandé)
*   Accès SSH root ou sudo
*   Python 3.10+ installé
*   PostgreSQL (ou conserver SQLite pour de très petits projets)

## 2. Sécuriser l'application

Dans votre fichier `settings.py` de production :

```python
# settings.py

# 🚨 SÉCURITÉ CRITIQUE
DEBUG = False

# Liste des domaines autorisés (ex: votre-domaine.com)
ALLOWED_HOSTS = ['votre-domaine.com', 'www.votre-domaine.com', 'ip-du-serveur']

# Paramètres de sécurité (HTTPS)
# SECURE_SSL_REDIRECT = True  # Décommenter une fois SSL actif
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
```

## 3. Gestion des Fichiers Statiques

En production, Django ne sert pas les fichiers statiques. Il faut les rassembler :

1.  Configurer `STATIC_ROOT` dans `settings.py` :
    ```python
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    ```
2.  Lancer la commande :
    ```bash
    python manage.py collectstatic
    ```

## 4. Installation des Outils de Production

Installer Gunicorn (serveur d'application WSGI) :

```bash
pip install gunicorn
```

Tester Gunicorn manuellement :
```bash
gunicorn gest_ecole.wsgi:application --bind 0.0.0.0:8000
```

## 5. Créer un Service Systemd (Gunicorn)

Créez le fichier `/etc/systemd/system/gunicorn.service` :

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/chemin/vers/gest_ecole
ExecStart=/chemin/vers/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/chemin/vers/gest_ecole/gest_ecole.sock gest_ecole.wsgi:application

[Install]
WantedBy=multi-user.target
```

Activez le service :
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 6. Configurer Nginx (Serveur Web)

Installer Nginx : `sudo apt install nginx`

Créez une config `/etc/nginx/sites-available/gest_ecole` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Servir les fichiers statiques
    location /static/ {
        root /chemin/vers/gest_ecole;
    }

    # Servir les fichiers médias (uploads)
    location /uploads/ {
        root /chemin/vers/gest_ecole;
    }

    # Proxy vers Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/chemin/vers/gest_ecole/gest_ecole.sock;
    }
}
```

Activez le site :
```bash
sudo ln -s /etc/nginx/sites-available/gest_ecole /etc/nginx/sites-enabled
sudo Nginx -t
sudo systemctl restart nginx
```

## 7. HTTPS (SSL Gratuit avec Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

---
[⬅ Retour aux Commandes Utiles](util.md)
