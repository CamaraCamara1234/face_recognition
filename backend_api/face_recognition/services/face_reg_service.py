from PIL import Image
import numpy as np
import cv2
import faiss
from insightface.app import FaceAnalysis
import torch
import random
import torchvision.transforms as T

# Initialisation de InsightFace avec le modèle ArcFace
face_app = FaceAnalysis(
    name="buffalo_l", 
    providers=['CUDAExecutionProvider' if torch.cuda.is_available() else 'CPUExecutionProvider']
)
face_app.prepare(ctx_id=0 if torch.cuda.is_available() else -1, det_size=(640, 640))

# ==================== Data augmentation forte ====================

def strong_augmentations(image: Image.Image):
    transform_list = [
        T.RandomHorizontalFlip(p=0.5),
        T.RandomRotation(degrees=20),
        T.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.2, hue=0.1),
        T.RandomPerspective(distortion_scale=0.2, p=0.5),
    ]
    augment = T.Compose([T.Resize((250, 250)), *transform_list, T.ToTensor()])
    augmentations = []

    for _ in range(5):
        aug_img = augment(image)
        aug_pil = T.ToPILImage()(aug_img)
        augmentations.append(aug_pil)

    return augmentations

# ==================== Embedding avec InsightFace ====================

def compute_robust_embedding_insightface(pil_img: Image.Image):
    embeddings = []
    augmentations = strong_augmentations(pil_img)

    for aug in augmentations:
        img_np = np.array(aug)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        faces = face_app.get(img_bgr)

        if faces:
            emb = faces[0].normed_embedding  # L2-normalisé
            embeddings.append(emb)

    if not embeddings:
        return None
    return np.median(np.stack(embeddings, axis=0), axis=0)

# ==================== Faiss – Recherche du plus proche voisin ====================

def get_closest_match(embedding, database_embeddings, ids, threshold=0.8):
    if not database_embeddings:
        return None, None

    d = len(embedding)
    index = faiss.IndexFlatL2(d)
    index.add(np.stack(database_embeddings))

    D, I = index.search(np.expand_dims(embedding, axis=0), 1)
    closest_distance = D[0][0]
    closest_index = I[0][0]

    if closest_distance < threshold:
        return ids[closest_index], closest_distance
    else:
        return None, closest_distance

def get_closest_match(embedding, database_embeddings, ids, threshold=0.8):
    if not database_embeddings:
        return None, None  # Aucun embedding dans la base

    d = len(embedding)
    index = faiss.IndexFlatL2(d)
    index.add(np.stack(database_embeddings))

    D, I = index.search(np.expand_dims(embedding, axis=0), 1)
    closest_distance = D[0][0]
    closest_index = I[0][0]

    if closest_distance < threshold:
        return ids[closest_index], closest_distance
    else:
        return None, closest_distance
