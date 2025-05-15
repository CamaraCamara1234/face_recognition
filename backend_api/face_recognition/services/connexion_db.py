import faiss
import numpy as np
import os
from django.conf import settings
import pickle

# Chemins de stockage
FAISS_INDEX_PATH = os.path.join(settings.BASE_DIR, 'data/faiss_index.index')
IDS_MAPPING_PATH = os.path.join(settings.BASE_DIR, 'data/ids_mapping.pkl')

class FaceDB:
    def __init__(self):
        self.index = None
        self.ids_mapping = []
        self.dimension = 512  # Dimension de vos embeddings (à adapter)
        
        self.load_db()

    def load_db(self):
        """Charge l'index FAISS et le mapping des IDs depuis le disque"""
        try:
            if os.path.exists(FAISS_INDEX_PATH):
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(IDS_MAPPING_PATH, 'rb') as f:
                    self.ids_mapping = pickle.load(f)
            else:
                self._init_new_db()
        except Exception as e:
            print(f"Erreur chargement DB: {str(e)}")
            self._init_new_db()

    def _init_new_db(self):
        """Initialise une nouvelle base vide"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.ids_mapping = []
        
        # Crée le dossier data si inexistant
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        self.save_db()

    def save_db(self):
        """Sauvegarde l'état actuel sur le disque"""
        try:
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            with open(IDS_MAPPING_PATH, 'wb') as f:
                pickle.dump(self.ids_mapping, f)
        except Exception as e:
            print(f"Erreur sauvegarde DB: {str(e)}")

    def add_face(self, embedding, user_id):
        """Ajoute un nouvel embedding à la base"""
        embedding = np.array(embedding).astype('float32').reshape(1, -1)
        self.index.add(embedding)
        self.ids_mapping.append(user_id)
        self.save_db()

    def search_face(self, embedding, threshold=0.8):
        """Recherche le visage le plus proche"""
        embedding = np.array(embedding).astype('float32').reshape(1, -1)
        D, I = self.index.search(embedding, 1)
        
        if I[0][0] == -1 or D[0][0] > threshold:
            return None, float(D[0][0])
        
        return self.ids_mapping[I[0][0]], float(D[0][0])

# Instance globale
face_db = FaceDB()