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
import datetime
import os
import base64
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import uuid
from PIL import Image
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
import onnxruntime as ort
from typing import Dict, List


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import shutil
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from api.services import PIDCheckService
from .services.service_detection_extraction import *
from django.test import RequestFactory

logger = logging.getLogger(__name__)


##### ###################################################
# train model on loaded images from api
# #######################################################
@csrf_exempt
def process_pending_users(request):
    """Endpoint pour traiter les utilisateurs en attente dans db_users"""
    if request.method == 'POST':
        try:
            db_users_dir = os.path.join(settings.MEDIA_ROOT, 'db_users')
            if not os.path.exists(db_users_dir):
                return JsonResponse({
                    'success': True,
                    'message': 'Aucun utilisateur en attente',
                    'processed': 0
                })

            processed_users = []
            failed_users = []
            user_dirs = [d for d in os.listdir(db_users_dir)
                         if os.path.isdir(os.path.join(db_users_dir, d))]

            for user_id in user_dirs:
                user_dir = os.path.join(db_users_dir, user_id)
                image_files = [f for f in os.listdir(user_dir)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

                if not image_files:
                    shutil.rmtree(user_dir)
                    continue

                # Prendre la première image trouvée
                image_path = os.path.join(user_dir, image_files[0])

                try:
                    # Préparer la requête pour register_face
                    with open(image_path, 'rb') as img_file:
                        image_data = img_file.read()

                    uploaded_file = SimpleUploadedFile(
                        name=image_files[0],
                        content=image_data,
                        content_type='image/jpeg'
                    )

                    # Créer une requête POST simulée
                    from django.test import RequestFactory
                    factory = RequestFactory()
                    mock_request = factory.post('/register_face/', {
                        'user_id': user_id,
                        'source': 'db_passenger'
                    })
                    mock_request.FILES['image'] = uploaded_file
                    # mock_request.FILES['source'] = 'db_passenger'

                    # Appeler register_face
                    from .views import register_face
                    response = register_face(mock_request)

                    if response.status_code == 200:
                        # Supprimer le dossier si l'enregistrement a réussi
                        shutil.rmtree(user_dir)
                        processed_users.append(user_id)
                    else:
                        failed_users.append({
                            'user_id': user_id,
                            'error': response.json().get('message')
                        })

                except Exception as e:
                    failed_users.append({
                        'user_id': user_id,
                        'error': str(e)
                    })

            return JsonResponse({
                'success': True,
                'message': 'Traitement terminé',
                'processed': len(processed_users),
                'successful_users': processed_users,
                'failed_users': failed_users
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors du traitement'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)


######################################################
# Load images and train model
# ####################################################
@api_view(['POST'])
def sync_and_process_all(request):
    """
    Endpoint combiné qui:
    1. Synchronise toutes les images des passagers
    2. Traite les utilisateurs en attente dans db_users
    """
    # Partie 1: Synchronisation des images des passagers
    passenger_results = {}
    try:
        service = PIDCheckService()
        passenger_results = service.process_all_passengers()
        success_count = sum(
            1 for r in passenger_results if r.get('status') == 'success')
        passenger_response = {
            "status": "completed",
            "passengers_processed": len(passenger_results),
            "images_saved": success_count,
            "details": passenger_results
        }
    except Exception as e:
        logger.error(f"Erreur dans sync_passenger_images: {str(e)}")
        passenger_response = {
            "status": "error",
            "message": str(e)
        }
        return Response({
            "sync_passengers": passenger_response,
            "process_pending_users": {
                "status": "not_executed",
                "message": "Arrêté en raison de l'échec de sync_passenger_images"
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Partie 2: Traitement des utilisateurs en attente
    pending_users_response = {}
    try:
        db_users_dir = os.path.join(settings.MEDIA_ROOT, 'db_users')
        if not os.path.exists(db_users_dir):
            pending_users_response = {
                'success': True,
                'message': 'Aucun utilisateur en attente',
                'processed': 0
            }
        else:
            processed_users = []
            failed_users = []
            user_dirs = [d for d in os.listdir(db_users_dir)
                         if os.path.isdir(os.path.join(db_users_dir, d))]

            for user_id in user_dirs:
                user_dir = os.path.join(db_users_dir, user_id)
                image_files = [f for f in os.listdir(user_dir)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

                if not image_files:
                    shutil.rmtree(user_dir)
                    continue

                # Prendre la première image trouvée
                image_path = os.path.join(user_dir, image_files[0])

                try:
                    with open(image_path, 'rb') as img_file:
                        image_data = img_file.read()

                    uploaded_file = SimpleUploadedFile(
                        name=image_files[0],
                        content=image_data,
                        content_type='image/jpeg'
                    )

                    factory = RequestFactory()
                    mock_request = factory.post('/register_face/', {
                        'user_id': user_id,
                        'source': 'db_passenger'
                    })
                    mock_request.FILES['image'] = uploaded_file

                    from .views import register_face
                    response = register_face(mock_request)

                    if response.status_code == 200:
                        shutil.rmtree(user_dir)
                        processed_users.append(user_id)
                    else:
                        failed_users.append({
                            'user_id': user_id,
                            'error': response.json().get('message')
                        })

                except Exception as e:
                    failed_users.append({
                        'user_id': user_id,
                        'error': str(e)
                    })

            pending_users_response = {
                'success': True,
                'message': 'Traitement terminé',
                'processed': len(processed_users),
                'successful_users': processed_users,
                'failed_users': failed_users
            }

    except Exception as e:
        pending_users_response = {
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du traitement'
        }

    # Retourner les deux résultats combinés
    return Response({
        "sync_passengers": passenger_response,
        "process_pending_users": pending_users_response
    }, status=status.HTTP_200_OK)


##### ###################################################
# loading, detection, extration and train
# #######################################################
@api_view(['POST'])
def sync_and_process_all(request):
    """
    Endpoint amélioré qui:
    1. Vide la base de données (appel à clear_database)
    2. Synchronise les images des passagers
    3. Traite les utilisateurs en attente avec:
       - Classification des documents
       - Extraction spéciale pour old_cni_recto
    """
    # Initialisation des services
    doc_classifier = DocumentClassifier()
    old_cni_extractor = OldCNIExtractor()
    pid_service = PIDCheckService()

    # # Étape 0: Vider la base de données avant traitement
    # try:
    #     clear_request = RequestFactory().post('/clear_database/')
    #     clear_response = clear_database(clear_request)
    #     if clear_response.status_code != status.HTTP_200_OK:
    #         logger.error("Échec du vidage de la base de données")
    #         return Response({
    #             "status": "error",
    #             "message": "Échec du vidage initial de la base de données"
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # except Exception as e:
    #     logger.error(f"Erreur lors du vidage de la base: {str(e)}")
    #     return Response({
    #         "status": "error",
    #         "message": f"Exception lors du vidage de la base: {str(e)}"
    #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Partie 1: Synchronisation des passagers
    try:
        passenger_results = pid_service.process_all_passengers()
        passenger_response = {
            "status": "completed",
            "passengers_processed": len(passenger_results),
            "images_saved": sum(1 for r in passenger_results if r.get('status') == 'success'),
            "details": passenger_results,
            "database_cleared": True
        }
    except Exception as e:
        logger.error(f"Erreur sync_passenger_images: {str(e)}")
        return Response({
            "status": "error",
            "message": f"Échec synchronisation: {str(e)}",
            "database_cleared": True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Partie 2: Traitement des utilisateurs en attente
    db_users_dir = os.path.join(settings.MEDIA_ROOT, 'db_users')
    if not os.path.exists(db_users_dir):
        return Response({
            "sync_passengers": passenger_response,
            "process_pending_users": {
                "status": "completed",
                "message": "Aucun utilisateur en attente",
                "processed": 0
            }
        })

    processed_users = []
    failed_users = []

    for user_id in os.listdir(db_users_dir):
        user_dir = os.path.join(db_users_dir, user_id)
        if not os.path.isdir(user_dir):
            continue

        image_files = [f for f in os.listdir(user_dir)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            shutil.rmtree(user_dir)
            continue

        image_path = os.path.join(user_dir, image_files[0])

        try:
            # Charger l'image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Impossible de charger {image_path}")

            # Étape 1: Classification du document
            classification = doc_classifier.classify(image)

            if classification['status'] != 'success':
                # Cas où aucun document n'est détecté ou erreur de classification
                logger.warning(
                    f"Aucun document détecté pour {user_id}, enregistrement direct de l'image")
                doc_type = 'unknown'
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            else:
                doc_type = classification['class_name']

                # Étape 2: Traitement spécial pour old_cni_recto
                if doc_type == 'old_cni_recto':
                    extracted_photo = old_cni_extractor.extract_photo_zone(
                        image)
                    if extracted_photo is not None:
                        _, img_encoded = cv2.imencode('.jpg', extracted_photo)
                        image_data = img_encoded.tobytes()
                    else:
                        logger.warning(
                            f"Zone photo non extraite pour {user_id}, utilisation de l'image complète")
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                else:
                    # Pour les autres types, utiliser l'image originale
                    with open(image_path, 'rb') as f:
                        image_data = f.read()

            # Étape 3: Enregistrement du visage
            uploaded_file = SimpleUploadedFile(
                name=image_files[0],
                content=image_data,
                content_type='image/jpeg'
            )

            mock_request = RequestFactory().post('/register_face/', {
                'user_id': user_id,
                'source': 'db_passenger',
                'doc_type': doc_type
            })
            mock_request.FILES['image'] = uploaded_file

            response = register_face(mock_request)

            print("x*x"*10)
            print(response.status_code)
            print("x*x"*10)
            if response.status_code == 200:
                shutil.rmtree(user_dir)
                processed_users.append({
                    'user_id': user_id,
                    'doc_type': doc_type,
                    'status': 'success'
                })
            else:
                failed_users.append({
                    'user_id': user_id,
                    'doc_type': doc_type,
                    'error': response.json().get('message', 'Unknown error'),
                    'status': 'failed'
                })

        except Exception as e:
            failed_users.append({
                'user_id': user_id,
                'error': str(e),
                'status': 'failed'
            })
            logger.error(f"Erreur traitement {user_id}: {str(e)}")

    return Response({
        "database_cleared": True,
        "sync_passengers": passenger_response,
        "process_pending_users": {
            "status": "completed",
            "processed": len(processed_users),
            "successful_users": processed_users,
            "failed_users": failed_users,
            "statistics": {
                "old_cni_recto_count": sum(1 for u in processed_users + failed_users if u.get('doc_type') == 'old_cni_recto'),
                "other_types_count": sum(1 for u in processed_users + failed_users if u.get('doc_type') != 'old_cni_recto'),
                "unknown_types_count": sum(1 for u in processed_users + failed_users if u.get('doc_type') == 'unknown')
            }
        }
    }, status=status.HTTP_200_OK)

########################################################
    # Add new face in faiss
# ######################################################


@csrf_exempt
def register_face(request):
    """Endpoint pour enregistrer un nouveau visage"""
    if request.method == 'POST':
        try:
            # 1. Validation des données
            user_id = request.POST.get('user_id')
            image_file = request.FILES.get('image')
            source = request.POST.get('source')

            if not user_id or not image_file:
                return JsonResponse({
                    'success': False,
                    'message': 'user_id et image sont requis'
                }, status=400)

            # print("=========> source : ", source)
            # 2. Vérification que l'utilisateur existe dans FAISS
            if face_db.user_exists(user_id):
                if source == 'db_passenger':
                    # Vérification du nom de l'image
                    user_dir = os.path.join(
                        settings.MEDIA_ROOT, 'db_users', user_id)
                    requested_image_name = f"{os.path.splitext(image_file.name)[0]}.jpg"

                    if os.path.exists(user_dir):
                        existing_images = os.listdir(user_dir)
                        if requested_image_name in existing_images:
                            return JsonResponse({
                                'success': False,
                                'message': f'Une image avec le même nom ({requested_image_name}) existe déjà pour cet utilisateur',
                                'user_id': user_id
                            }, status=400)

                    # Créer une requête POST simulée pour update_face
                    from django.test import RequestFactory
                    factory = RequestFactory()
                    mock_request = factory.post('/update_face/', {
                        'user_id': user_id,
                        'source': source
                    })
                    mock_request.FILES = request.FILES  # Transférer les fichiers

                    # Appeler update_face
                    from .views import update_face
                    return update_face(mock_request)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': f'L\'utilisateur {user_id} existe déjà'
                    }, status=404)

            # 3. Création du répertoire utilisateur si inexistant
            user_dir = os.path.join(settings.MEDIA_ROOT, 'data', user_id)
            os.makedirs(user_dir, exist_ok=True)

            # 4. Sauvegarde de l'image originale
            if source == 'web':
                unique_filename = f"{uuid.uuid4().hex}.jpg"
            elif source == 'db_passenger':
                filename_with_extension = image_file.name
                unique_filename = f"{os.path.splitext(filename_with_extension)[0]}.jpg"
            else:
                unique_filename = f"{uuid.uuid4().hex}.jpg"
            image_path = os.path.join(user_dir, unique_filename)

            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            # 5. Traitement de l'image
            image = Image.open(image_file).convert('RGB')
            embedding = compute_robust_embedding_insightface(image)

            if embedding is None:
                # Suppression de l'image si aucun visage détecté

                print("le probeleme est ici :",)
                if os.path.exists(image_path):
                    os.remove(image_path)
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun visage détecté dans l\'image'
                }, status=400)

            # 6. Enregistrement dans FAISS
            face_db.add_face(embedding, user_id)

            return JsonResponse({
                'success': True,
                'message': f'Visage enregistré avec l\'ID: {user_id}',
                'embedding_shape': embedding.shape,
                'image_path': os.path.join('media', 'data', user_id, unique_filename)
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
def update_face(request):
    """Endpoint pour mettre à jour le visage d'un utilisateur existant"""
    if request.method == 'POST':
        try:
            # 1. Validation des données
            user_id = request.POST.get('user_id')
            image_file = request.FILES.get('image')
            source = request.FILES.get('source')

            if not user_id or not image_file:
                return JsonResponse({
                    'success': False,
                    'message': 'user_id et image sont requis'
                }, status=400)

            # 2. Vérification que l'utilisateur existe dans FAISS
            if not face_db.user_exists(user_id):
                return JsonResponse({
                    'success': False,
                    'message': f'L\'utilisateur {user_id} n\'existe pas'
                }, status=404)

            # 3. Traitement de la nouvelle image
            image = Image.open(image_file).convert('RGB')
            new_embedding = compute_robust_embedding_insightface(image)

            if new_embedding is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun visage détecté dans la nouvelle image'
                }, status=400)

            # 4. Vérification que la nouvelle image correspond à l'utilisateur
            # Récupérer l'ancien embedding pour comparaison
            old_embedding = face_db.get_face_embedding(user_id)
            if old_embedding is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Impossible de récupérer l\'ancien visage'
                }, status=400)

            # Calculer la similarité entre les embeddings
            similarity = face_db.compare_embeddings(
                old_embedding, new_embedding)

            # Définir un seuil de similarité (à ajuster selon votre modèle)
            SIMILARITY_THRESHOLD = 0.6

            if similarity < SIMILARITY_THRESHOLD:
                return JsonResponse({
                    'success': False,
                    'message': 'La nouvelle image ne correspond pas suffisamment à l\'utilisateur',
                    'similarity_score': float(similarity),
                    'threshold': float(SIMILARITY_THRESHOLD)
                }, status=400)

            # 5. Suppression des anciennes images
            user_dir = os.path.join(settings.MEDIA_ROOT, 'data', user_id)
            if os.path.exists(user_dir):
                # Supprimer tous les fichiers dans le dossier utilisateur
                for filename in os.listdir(user_dir):
                    file_path = os.path.join(user_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(
                            f'Erreur lors de la suppression de {file_path}: {e}')

            # 6. Sauvegarde de la nouvelle image
            os.makedirs(user_dir, exist_ok=True)
            if source == 'web':
                unique_filename = f"{uuid.uuid4().hex}.jpg"
            elif source == 'db_passenger':
                filename_with_extension = image_file.name
                unique_filename = f"{os.path.splitext(filename_with_extension)[0]}.jpg"
            else:
                unique_filename = f"{uuid.uuid4().hex}.jpg"

            image_path = os.path.join(user_dir, unique_filename)

            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            # 7. Mise à jour dans FAISS
            face_db.update_face(user_id, new_embedding)

            return JsonResponse({
                'success': True,
                'message': f'Visage mis à jour pour l\'ID: {user_id}',
                'embedding_shape': new_embedding.shape,
                'new_image_path': os.path.join('media', 'data', user_id, unique_filename),
                'similarity_score': float(similarity)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la mise à jour'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)


@csrf_exempt
def verify_face_topn(request):
    """Endpoint pour reconnaître un visage et retourner le top 3 des correspondances"""
    if request.method == 'POST':
        try:
            image_file = request.FILES.get('image')
            threshold = float(request.POST.get('threshold', 0.8))
            top_n = int(request.POST.get('top_n', 3))

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

            # Récupérer les top 3 correspondances
            matches = face_db.search_face_topn(
                embedding, threshold, top_n=top_n)

            # Si c'est un tuple unique (ancienne version), le convertir en liste
            if isinstance(matches, tuple):
                matches = [matches] if matches[0] is not None else []

            # Préparer les données de réponse
            matches_data = []
            for match in matches:
                matched_id, distance = match
                percentage = max(
                    0, min(100, 100 - (distance / threshold) * 35))

                match_data = {
                    'user_id': matched_id,
                    'passenger_id': None,  # Initialisé à None par défaut
                    'distance': distance,
                    'percentage': round(percentage, 1),
                    'message': f'Visage reconnu: {matched_id}' if matched_id else 'Aucune correspondance'
                }

                # Ajouter l'image et passenger_id si l'utilisateur est identifié
                if matched_id:
                    user_dir = os.path.join(
                        settings.MEDIA_ROOT, 'data', matched_id)
                    if os.path.exists(user_dir):
                        try:
                            image_files = [
                                f for f in os.listdir(user_dir)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                            ]

                            if image_files:
                                image_files.sort(
                                    key=lambda x: os.path.getmtime(
                                        os.path.join(user_dir, x)),
                                    reverse=True
                                )
                                latest_image = image_files[0]
                                image_path = os.path.join(
                                    user_dir, latest_image)

                                # Extraire le passenger_id (nom du fichier sans extension)
                                passenger_id = os.path.splitext(
                                    latest_image)[0]
                                match_data['passenger_id'] = passenger_id

                                with open(image_path, "rb") as img_file:
                                    encoded_image = base64.b64encode(
                                        img_file.read()).decode('utf-8')

                                match_data['user_image'] = f"data:image/jpeg;base64,{encoded_image}"
                        except Exception as e:
                            print(
                                f"Erreur lors de la récupération de l'image: {str(e)}")

                matches_data.append(match_data)

            # Préparer la réponse globale
            has_match = any(match['user_id'] for match in matches_data)
            response_data = {
                'success': has_match,
                'matched': has_match,
                'matches': matches_data,
                'threshold': threshold,
                'message': 'Correspondances trouvées' if has_match else 'Aucune correspondance trouvée'
            }

            return JsonResponse(response_data)

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
def user_exists(request):
    """Endpoint pour vérifier si un utilisateur existe dans la base"""
    if request.method == 'GET':
        try:
            user_id = request.GET.get('user_id')
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': 'user_id est requis'
                }, status=400)

            exists = face_db.user_exists(user_id)

            return JsonResponse({
                'success': True,
                'exists': exists,
                'user_id': user_id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
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


@csrf_exempt
def delete_user(request):
    """Endpoint corrigé pour supprimer un utilisateur"""
    if request.method == 'DELETE':
        try:
            user_id = request.GET.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'message': 'Paramètre user_id manquant'}, status=400)

            # Charger les données
            index = faiss.read_index('data/faiss_index.index')
            with open('data/ids_mapping.pkl', 'rb') as f:
                ids_mapping = pickle.load(f)

            # Vérifier si l'utilisateur existe
            if user_id not in ids_mapping:
                return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé'}, status=404)

            # Trouver tous les indices correspondants
            indices = [i for i, x in enumerate(ids_mapping) if x == user_id]

            if not indices:
                return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé'}, status=404)

            # Supprimer de FAISS (en ordre inverse pour éviter les décalages)
            for idx in sorted(indices, reverse=True):
                if isinstance(index, faiss.IndexFlatL2):
                    ntotal = index.ntotal
                    if ntotal == 1:
                        # Cas spécial: suppression du dernier élément
                        index.reset()
                    else:
                        # Reconstruire l'index sans l'élément supprimé
                        xb = []
                        for i in range(ntotal):
                            if i != idx:
                                vec = index.reconstruct(i)
                                xb.append(vec)

                        if xb:  # Vérifier qu'il reste des vecteurs
                            xb = np.array(xb)
                            index.reset()
                            index.add(xb)
                else:
                    index.remove_ids(np.array([idx]))

                # Supprimer du mapping
                ids_mapping.pop(idx)

            # Sauvegarder les modifications
            faiss.write_index(index, 'data/faiss_index.index')
            with open('data/ids_mapping.pkl', 'wb') as f:
                pickle.dump(ids_mapping, f)

            # Supprimer le dossier de l'utilisateur s'il existe
            user_dir = os.path.join('media/data', user_id)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)

            # os.kill(os.getpid(), signal.SIGINT)
            return JsonResponse({'success': True, 'message': f'Utilisateur {user_id} supprimé', 'remaining': len(ids_mapping)})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# @csrf_exempt
# def clear_database(request):
#     """Vidage radical mais contrôlé de la base"""
#     if request.method != 'POST':
#         return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

#     try:
#         # 1. Suppression complète du dossier data
#         data_dir = 'data'
#         temp_dir = 'data_temp_backup'

#         # Sauvegarde temporaire (optionnel)
#         if os.path.exists(data_dir):
#             shutil.move(data_dir, temp_dir)

#         # 2. Recréation de la structure
#         os.makedirs(data_dir, exist_ok=True)

#         # 3. Réinitialisation des fichiers
#         dimension = 512
#         index = faiss.IndexFlatL2(dimension)
#         faiss.write_index(index, os.path.join(data_dir, 'faiss_index.index'))

#         with open(os.path.join(data_dir, 'ids_mapping.pkl'), 'wb') as f:
#             pickle.dump([], f)

#         # 4. Nettoyage des utilisateurs (media/data)
#         media_data_dir = os.path.join('media', 'data')
#         if os.path.exists(media_data_dir):
#             shutil.rmtree(media_data_dir)
#             os.makedirs(media_data_dir)

#         # 5. Nettoyage final
#         if os.path.exists(temp_dir):
#             shutil.rmtree(temp_dir)

#         return JsonResponse({
#             'success': True,
#             'message': 'Base réinitialisée radicalement',
#             'details': {
#                 'faiss_recreated': True,
#                 'mapping_reset': True,
#                 'media_data_cleaned': True
#             }
#         })

#     except Exception as e:
#         # Rollback en cas d'échec
#         if os.path.exists(temp_dir) and not os.path.exists(data_dir):
#             shutil.move(temp_dir, data_dir)

#         logger.critical(f"ERREUR RADICALE: {str(e)}", exc_info=True)
#         return JsonResponse({
#             'success': False,
#             'error': str(e),
#             'message': 'Échec de la réinitialisation radicale',
#             'restored_backup': os.path.exists(data_dir)
#         }, status=500)


def force_reload_faiss_structures():
    """Force le rechargement de toutes les structures FAISS en mémoire"""
    global faiss_index, ids_mapping, embeddings_cache  # Adaptez selon vos variables

    data_dir = 'data'

    try:
        # Rechargement de l'index FAISS
        index_path = os.path.join(data_dir, 'faiss_index.index')
        if os.path.exists(index_path):
            faiss_index = faiss.read_index(index_path)
        else:
            # Si pas d'index, créer un nouveau
            dimension = 512
            faiss_index = faiss.IndexFlatL2(dimension)

        # Rechargement du mapping des IDs
        mapping_path = os.path.join(data_dir, 'ids_mapping.pkl')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'rb') as f:
                ids_mapping = pickle.load(f)
        else:
            ids_mapping = []

        # Vider les caches s'ils existent
        if 'embeddings_cache' in globals():
            embeddings_cache.clear()

        # Cache Django
        from django.core.cache import cache
        cache.clear()

        return True, "Structures rechargées avec succès"

    except Exception as e:
        return False, f"Erreur lors du rechargement: {str(e)}"


@csrf_exempt
def reload_memory_structures(request):
    """Endpoint pour forcer le rechargement des structures en mémoire"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    success, message = force_reload_faiss_structures()

    return JsonResponse({
        'success': success,
        'message': message
    })

# Version améliorée de votre fonction clear_database


@csrf_exempt
def clear_database(request):
    """Vidage radical avec rechargement automatique"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        # Votre code de nettoyage existant...
        data_dir = 'data'
        temp_dir = 'data_temp_backup'

        if os.path.exists(data_dir):
            shutil.move(data_dir, temp_dir)

        os.makedirs(data_dir, exist_ok=True)

        dimension = 512
        index = faiss.IndexFlatL2(dimension)
        faiss.write_index(index, os.path.join(data_dir, 'faiss_index.index'))

        with open(os.path.join(data_dir, 'ids_mapping.pkl'), 'wb') as f:
            pickle.dump([], f)

        media_data_dir = os.path.join('media', 'data')
        if os.path.exists(media_data_dir):
            shutil.rmtree(media_data_dir)
            os.makedirs(media_data_dir)

        # CRUCIAL: Rechargement forcé après nettoyage
        success, reload_message = force_reload_faiss_structures()

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        return JsonResponse({
            'success': True,
            'message': 'Base réinitialisée avec rechargement forcé',
            'reload_status': success,
            'reload_message': reload_message,
            'details': {
                'faiss_recreated': True,
                'mapping_reset': True,
                'media_data_cleaned': True,
                'memory_reloaded': success
            }
        })

    except Exception as e:
        if os.path.exists(temp_dir) and not os.path.exists(data_dir):
            shutil.move(temp_dir, data_dir)

        logger.critical(f"ERREUR RADICALE: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Échec de la réinitialisation radicale'
        }, status=500)

##################################
    # Liste des users
##################################


@csrf_exempt
def list_users(request):
    """Nouvel endpoint pour lister les utilisateurs"""
    try:
        with open('data/ids_mapping.pkl', 'rb') as f:
            ids_mapping = pickle.load(f)

        # Si vous stockez des timestamps, sinon générez une date fictive
        users = [{
            'id': uid,
            'timestamp': datetime.now().isoformat()  # À adapter
        } for uid in ids_mapping]

        return JsonResponse({
            'success': True,
            'users': users,
            'count': len(users)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def list_pending_users(request):
    """Endpoint pour lister les utilisateurs en attente dans db_users"""
    if request.method == 'GET':
        try:
            db_users_dir = os.path.join(settings.MEDIA_ROOT, 'db_users')
            if not os.path.exists(db_users_dir):
                return JsonResponse({
                    'success': True,
                    'message': 'Aucun utilisateur en attente',
                    'pending_users': []
                })

            # Récupérer la liste des dossiers d'utilisateurs
            user_dirs = [d for d in os.listdir(db_users_dir)
                         if os.path.isdir(os.path.join(db_users_dir, d))]

            pending_users = []

            for user_id in user_dirs:
                user_dir = os.path.join(db_users_dir, user_id)
                image_files = [f for f in os.listdir(user_dir)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

                if image_files:  # Ne considérer que les dossiers avec des images
                    pending_users.append({
                        'user_id': user_id,
                        'images_count': len(image_files),
                        'images': image_files
                    })

            return JsonResponse({
                'success': True,
                'pending_users_count': len(pending_users),
                'pending_users': pending_users
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la récupération des utilisateurs en attente'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    }, status=405)
