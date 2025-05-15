# 🧠 Système de Reconnaissance Faciale

![Demo](FACE_RECOGNITION_FRONTEND/public/demo.gif)  
<sub><i>Ajoutez une capture d’écran plus représentative si possible.</i></sub>

---

## 📁 Structure du Projet
````
FACE_RECOGNITION/
├── backend_api/ # API Django (serveur)
│ ├── face_recognition/ # Application principale
│ │ ├── migrations/
│ │ ├── services/ # Logique métier
│ │ │ ├── connection_db.py # Connexion à la base FAISS
│ │ │ └── face_utils.py # Utilitaires liés à la vision
│ │ ├── views.py # Endpoints API
│ │ ├── urls.py # Routing
│ │ └── ...
│ └── manage.py
│
├── env/ # Environnement virtuel Python
│ └── ...
│
└── FACE_RECOGNITION_FRONTEND/ # Application frontend React
├── public/
├── src/
│ ├── components/
│ │ ├── FaceRegister.jsx # Enregistrement facial
│ │ ├── FaceSearch.jsx # Recherche de visage
│ │ └── FaceStats.jsx # Statistiques et visualisation
│ └── App.js # Routing principal
└── package.json
``````



---

## 🚀 Fonctionnalités

### 🧩 Backend (Django + FAISS)
- **Enregistrement facial** :
  - Extraction d'embeddings avec *InsightFace*
  - Stockage dans un index FAISS pour la recherche rapide
  - Augmentation des données pour améliorer la robustesse

- **Reconnaissance** :
  - Recherche de similarité basée sur la distance cosine
  - Seuil configurable (valeur par défaut : `0.8`)
  - Affichage d’un pourcentage de confiance (ex. : 65% au seuil)

- **Statistiques système** :
  - Nombre total de visages enregistrés
  - Type d’index FAISS utilisé
  - Date de la dernière mise à jour

---

### 🎨 Frontend (React.js)
- **Interface utilisateur fluide** :
  - Capture de visage via webcam ou import d’image
  - Résultats affichés avec pourcentage de confiance
  - Barre de progression visuelle pour l’UX

- **Gestion simplifiée** :
  - Enregistrement avec identifiant utilisateur
  - Affichage des statistiques de reconnaissance
  - Feedback en temps réel à l'utilisateur

---

## ✅ Prérequis

- **Python** ≥ 3.8  
- **Node.js** ≥ 16  
- **PostgreSQL** (optionnel pour production)  
- **CUDA** (recommandé pour accélération GPU via InsightFace)

---

## ⚙️ Installation

### 🛠 Backend

```bash
cd FACE_RECOGNITION/backend_api

# Création et activation de l'environnement virtuel
python -m venv ../env
source ../env/bin/activate        # Linux/Mac
../env/Scripts/activate           # Windows
```

# Installation des dépendances
```bash
pip install -r requirements.txt
```

# Initialisation de la base de données
```bash
python manage.py migrate
```

# Lancement du serveur
```bash
python manage.py runserver
```
# 🌐 Frontend
```bash
cd FACE_RECOGNITION_FRONTEND
```

# Installation des dépendances
```bash
npm install
```

# Démarrage de l'application
```bash
npm start
```

### 📡 API - Endpoints disponibles
```

| Endpoint              | Méthode | Description                       |
| --------------------- | ------- | --------------------------------- |
| `/api/faces/register` | POST    | Enregistre un nouveau visage      |
| `/api/faces/verify`   | POST    | Recherche un visage dans la base  |
| `/api/faces/stats`    | GET     | Récupère les statistiques système |
```

## 📌 Remarques

Le seuil de reconnaissance peut être modifié dans la configuration backend.

Il est recommandé d'utiliser un GPU pour améliorer la performance du traitement d’images.

L’index FAISS peut être sauvegardé et rechargé pour éviter la reconstruction à chaque démarrage.

