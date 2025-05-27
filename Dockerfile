# Étape 1 : Base
FROM python:3.10-slim

# Étape 2 : Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Étape 3 : Install dépendances système (build + image)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Étape 4 : Créer dossier de travail
WORKDIR /app

# Étape 5 : Copier fichiers requirements et installer
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Étape 6 : Copier le reste du code
COPY . .

# ✅ Étape 6.5 : Créer dossier FAISS avec permissions
RUN mkdir -p /app/data && chmod -R 777 /app/data
RUN mkdir -p /app/media && chmod -R 777 /app/media

# Étape 7 : Port exposé (modifie si besoin)
EXPOSE 8000

# Étape 8 : Commande de lancement
CMD ["python", "backend_api/manage.py", "runserver", "0.0.0.0:8000"]
