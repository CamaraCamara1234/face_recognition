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

            # 2. Création du répertoire utilisateur si inexistant
            user_dir = os.path.join(settings.MEDIA_ROOT, 'data', user_id)
            os.makedirs(user_dir, exist_ok=True)

            # 3. Sauvegarde de l'image originale
            unique_filename = f"{uuid.uuid4().hex}.jpg"
            image_path = os.path.join(user_dir, unique_filename)
            
            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            # 4. Traitement de l'image
            image = Image.open(image_file).convert('RGB')
            embedding = compute_robust_embedding_insightface(image)

            if embedding is None:
                # Suppression de l'image si aucun visage détecté
                if os.path.exists(image_path):
                    os.remove(image_path)
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun visage détecté dans l\'image'
                }, status=400)

            # 5. Enregistrement dans FAISS
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
            percentage = max(0, min(100, 100 - (distance / threshold) * 35))
            
            response_data = {
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
            }

            # Si un utilisateur est identifié, chercher sa dernière image enregistrée
            if matched_id:
                user_dir = os.path.join(settings.MEDIA_ROOT, 'data', matched_id)
                
                if os.path.exists(user_dir):
                    # Trouver le fichier image le plus récent
                    try:
                        image_files = [
                            f for f in os.listdir(user_dir) 
                            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
                        ]
                        
                        if image_files:
                            # Trier par date de modification (le plus récent en premier)
                            image_files.sort(
                                key=lambda x: os.path.getmtime(os.path.join(user_dir, x)),
                                reverse=True
                            )
                            latest_image = image_files[0]
                            image_path = os.path.join(user_dir, latest_image)
                            
                            # Encoder l'image en base64
                            with open(image_path, "rb") as image_file:
                                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                            
                            response_data['user_image'] = f"data:image/jpeg;base64,{encoded_image}"
                    except Exception as e:
                        # Ne pas échouer si problème avec l'image
                        print(f"Erreur lors de la récupération de l'image: {str(e)}")

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

            # Sauvegarder
            faiss.write_index(index, 'data/faiss_index.index')
            with open('data/ids_mapping.pkl', 'wb') as f:
                pickle.dump(ids_mapping, f)

            return JsonResponse({'success': True, 'message': f'Utilisateur {user_id} supprimé', 'remaining': len(ids_mapping)})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def clear_database(request):
    """Endpoint corrigé pour vider la base"""
    if request.method == 'POST':
        try:
            dimension = 512  # Doit correspondre à votre modèle
            index = faiss.IndexFlatL2(dimension)

            # Réinitialiser complètement
            faiss.write_index(index, 'data/faiss_index.index')
            with open('data/ids_mapping.pkl', 'wb') as f:
                pickle.dump([], f)

            # Vérification
            index = faiss.read_index('data/faiss_index.index')
            with open('data/ids_mapping.pkl', 'rb') as f:
                ids_mapping = pickle.load(f)

            if index.ntotal == 0 and len(ids_mapping) == 0:
                return JsonResponse({'success': True, 'message': 'Base complètement vidée'})
            else:
                return JsonResponse({'success': False, 'message': 'La suppression a échoué'}, status=500)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

# Liste des users


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
