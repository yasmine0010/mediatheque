# Utiliser l'image officielle de Python comme base
FROM python:3.9-slim

# Définir le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le répertoire de travail
COPY requirements.txt .

# Installer les dépendances depuis requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers de l'application dans le conteneur
COPY . .

# Exposer le port sur lequel l'application sera accessible
EXPOSE 5000

# Commande pour démarrer l'application avec Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
