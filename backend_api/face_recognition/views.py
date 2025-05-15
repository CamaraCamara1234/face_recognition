from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
from django.conf import settings
from PIL import Image
import cv2
import numpy as np
from .services.face_reg_service import *
import json
from .services.connexion_db import *


# # Simule la base (à remplacer par une base réelle ou pickle plus tard)
# database_embeddings = []
# ids = []

# @csrf_exempt
# def register_face(request):
#     if request.method == 'POST':
#         try:
#             # Récupération des données
#             user_id = request.POST.get('user_id')
#             image_file = request.FILES.get('image')

#             if not user_id or not image_file:
#                 return JsonResponse({'success': False, 'message': 'user_id ou image manquant.'}, status=400)

#             # Conversion de l'image
#             image = Image.open(image_file).convert('RGB')

#             # Extraction des embeddings
#             embedding = compute_robust_embedding_insightface(image)
#             if embedding is None:
#                 return JsonResponse({'success': False, 'message': 'Aucun visage détecté.'}, status=400)

#             # Ajout à la base (à remplacer par une base persistante)
#             database_embeddings.append(embedding)
#             ids.append(user_id)

#             return JsonResponse({'success': True, 'message': f'Utilisateur {user_id} enregistré.'})

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=500)
#     else:
#         return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

# @csrf_exempt
# def verify_face1(request):
#     if request.method == 'POST':
#         try:
#             image_file = request.FILES.get('image')
#             if not image_file:
#                 return JsonResponse({'success': False, 'message': 'Image manquante.'}, status=400)

#             image = Image.open(image_file).convert('RGB')

#             embedding = compute_robust_embedding_insightface(image)
#             if embedding is None:
#                 return JsonResponse({'success': False, 'message': 'Aucun visage détecté.'}, status=400)

#             # Recherche dans la base
#             matched_id, distance = get_closest_match(embedding, database_embeddings, ids)

#             if matched_id is not None:
#                 return JsonResponse({
#                     'success': True,
#                     'matched_user_id': matched_id,
#                     'distance': float(distance),
#                     'message': f'Utilisateur reconnu comme {matched_id}'
#                 })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'matched_user_id': None,
#                     'distance': float(distance) if distance is not None else None,
#                     'message': 'Aucune correspondance trouvée'
#                 })

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=500)
#     else:
#         return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)


@csrf_exempt
def register_face(request):
    """Endpoint pour enregistrer un nouveau visage"""
    if request.method == 'POST':
        try:
            # 1. Validation des données
            user_id = request.POST.get('user_id')
            image_file = request.FILES.get('image')

            if not user_id or not image_file:
                return JsonResponse({
                    'success': False,
                    'message': 'user_id et image sont requis'
                }, status=400)

            # 2. Traitement de l'image
            image = Image.open(image_file).convert('RGB')
            embedding = compute_robust_embedding_insightface(image)

            if embedding is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun visage détecté dans l\'image'
                }, status=400)

            # 3. Enregistrement dans FAISS
            face_db.add_face(embedding, user_id)

            return JsonResponse({
                'success': True,
                'message': f'Visage enregistré avec l\'ID: {user_id}',
                'embedding_shape': embedding.shape
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'enregistrement'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)


@csrf_exempt
def verify_face(request):
    """Endpoint pour reconnaître un visage"""
    if request.method == 'POST':
        try:
            image_file = request.FILES.get('image')
            threshold = float(request.POST.get('threshold', 0.8))

            if not image_file:
                return JsonResponse({
                    'success': False,
                    'message': 'L\'image est requise'
                }, status=400)

            image = Image.open(image_file).convert('RGB')
            embedding = compute_robust_embedding_insightface(image)

            if embedding is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun visage détecté dans l\'image'
                }, status=400)

            matched_id, distance = face_db.search_face(embedding, threshold)

            # Calcul du pourcentage (65% au seuil, 100% à distance 0)
            percentage = max(0, min(100, 100 - (distance / threshold) * 35))

            return JsonResponse({
                'success': matched_id is not None,
                'matched': matched_id is not None,
                'user_id': matched_id,
                'distance': distance,
                'percentage': round(percentage, 1),
                'threshold': threshold,
                'message': (
                    f'Visage reconnu: {matched_id}' if matched_id
                    else 'Aucune correspondance trouvée'
                )
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la reconnaissance'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)


@csrf_exempt
def face_stats(request):
    """Endpoint pour obtenir des statistiques"""
    if request.method == 'GET':
        try:
            return JsonResponse({
                'success': True,
                'count': len(face_db.ids_mapping),
                'dimension': face_db.dimension,
                'index_type': str(face_db.index),
                'last_update': face_db.last_update.isoformat() if hasattr(face_db, 'last_update') else None
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)
