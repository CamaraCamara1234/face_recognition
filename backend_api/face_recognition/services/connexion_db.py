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
    
    def user_exists(self, user_id):
        """Vérifie si l'utilisateur existe dans la base"""
        return user_id in self.ids_mapping

    def get_face_index(self, user_id):
        """Retourne l'index de l'embedding pour un user_id donné"""
        try:
            return self.ids_mapping.index(user_id)
        except ValueError:
            return -1

    def remove_face(self, user_id):
        """Supprime un embedding de la base"""
        idx = self.get_face_index(user_id)
        if idx == -1:
            return False
        
        # Crée un nouveau index sans l'embedding à supprimer
        new_index = faiss.IndexFlatL2(self.dimension)
        
        # Récupère tous les embeddings sauf celui à supprimer
        all_embeddings = self.index.reconstruct_n(0, self.index.ntotal)
        mask = [i for i in range(len(self.ids_mapping)) if i != idx]
        
        if len(mask) > 0:
            filtered_embeddings = all_embeddings[mask]
            new_index.add(filtered_embeddings)
        
        # Met à jour les références
        self.index = new_index
        self.ids_mapping.pop(idx)
        self.save_db()
        return True

    def update_face(self, user_id, new_embedding):
        """Met à jour l'embedding pour un user_id donné"""
        # 1. Supprime l'ancien embedding
        self.remove_face(user_id)
        
        # 2. Ajoute le nouveau embedding
        self.add_face(new_embedding, user_id)
        
        return True
    
    def get_face_embedding(self, user_id):
        """Récupère l'embedding existant d'un utilisateur"""
        idx = self.get_face_index(user_id)
        if idx == -1:
            return None
            
        # FAISS ne fournit pas directement une méthode get, donc on reconstruit tout
        all_embeddings = self.index.reconstruct_n(0, self.index.ntotal)
        return all_embeddings[idx]

    def compare_embeddings(self, embedding1, embedding2):
        """Calcule la similarité cosinus entre deux embeddings"""
        embedding1 = np.array(embedding1).flatten()
        embedding2 = np.array(embedding2).flatten()
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

# Instance globale
face_db = FaceDB()