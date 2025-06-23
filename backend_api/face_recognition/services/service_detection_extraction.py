import cv2
import numpy as np
import logging
from typing import Dict, List, Optional
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ultralytics import YOLO
import os

logger = logging.getLogger(__name__)


class DocumentClassifier:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(
            settings.BASE_DIR, 'models', 'carte_classification', 'best.onnx')
        self.model = YOLO(self.model_path)
        self.class_names = {
            0: 'new_cni_recto',
            1: 'new_cni_verso',
            2: 'old_cni_recto',
            3: 'old_cni_verso',
            4: 'passeport',
            5: 'permis_recto',
            6: 'permis_verso'
        }

    def classify(self, image: np.ndarray) -> Dict:
        """Classifie le type de document"""
        try:
            results = self.model.predict(source=image, conf=0.5)
            result = results[0]

            if len(result.boxes) == 0:
                return {"status": "error", "message": "Aucun document détecté"}

            # Prendre la prédiction avec la plus haute confiance
            best_idx = np.argmax([box.conf for box in result.boxes])
            class_id = int(result.boxes[best_idx].cls)
            confidence = float(result.boxes[best_idx].conf)

            print("###"*10)
            print(self.class_names[class_id])
            print("###"*10)
            return {
                "status": "success",
                "class_name": self.class_names[class_id],
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Erreur classification document: {str(e)}")
            return {"status": "error", "message": str(e)}


class OldCNIExtractor:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(
            settings.BASE_DIR, 'models', 'cin_recto', 'best.onnx')
        self.model = YOLO(self.model_path)
        self.zone_names = {
            0: "nom",
            1: "prenom",
            2: "date_naissance",
            3: "ville",
            4: "date_expiration",
            5: "cin",
            6: "nom_ar",
            7: "prenom_ar",
            8: "ville_ar",
            9: "photo",
            10: "photo_portrait"
        }

    def extract_photo_zone(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extrait uniquement la zone photo d'une ancienne CNI recto"""
        try:
            results = self.model.predict(source=image, conf=0.7)
            result = results[0]

            # Trouver la zone 'photo' avec la plus haute confiance
            photo_boxes = []
            for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                if int(cls_id) == 9:  # 9 = photo (selon votre zone_names)
                    photo_boxes.append((box, float(conf)))

            if not photo_boxes:
                return None

            # Prendre la photo avec la plus haute confiance
            best_box = max(photo_boxes, key=lambda x: x[1])[0]
            x1, y1, x2, y2 = map(int, best_box)
            return image[y1:y2, x1:x2]

        except Exception as e:
            logger.error(f"Erreur extraction zone photo: {str(e)}")
            return None
