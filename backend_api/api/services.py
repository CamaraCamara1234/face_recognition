import os
import base64
import requests
from django.conf import settings
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class PIDCheckService:
    def __init__(self):
        self.base_url = "http://oidc.xayone.com:8080/ws-trust"
        self.auth_url = f"{self.base_url}/public/pid/managers/means/password/auth"
        self.credentials = {
            "username": "nab.harakat@gmail.com",
            "password": "Gaia1234"
        }
        self.subscription_id = "67ba6c6bdda7a5954b8db1dc"
        self.token = None
        self.session = self._configure_session()

    def _configure_session(self):
        """Configure une session avec retry policy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def authenticate(self):
        """Récupère le token d'authentification"""
        try:
            response = self.session.post(
                self.auth_url,
                json=self.credentials,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            self.token = response.json().get('accessToken')
            logger.info("Authentification réussie")
            return self.token
        except Exception as e:
            logger.error(f"Erreur d'authentification: {str(e)}")
            raise ConnectionError(f"Échec de l'authentification: {str(e)}")

    def get_passengers(self):
        """Récupère la liste des passagers"""
        if not self.token:
            self.authenticate()

        url = f"{self.base_url}/pid/passengers?subscriptionId={self.subscription_id}"
        try:
            response = self.session.get(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération des passagers: {str(e)}")
            raise ConnectionError(
                f"Échec de récupération des passagers: {str(e)}")

    def get_passenger_details(self, passenger_id):
        """Récupère les détails d'un passager"""
        if not self.token:
            self.authenticate()

        url = f"{self.base_url}/pid/passengers/{passenger_id}"
        try:
            response = self.session.get(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(
                f"Erreur lors de la récupération des détails du passager {passenger_id}: {str(e)}")
            raise ConnectionError(
                f"Échec de récupération des détails du passager: {str(e)}")
        
    def save_passenger_image(self, national_identifier, passenger_id, image_data):
        """Sauvegarde l'image d'un passager en vidant le dossier existant au préalable"""
        if not image_data:
            logger.warning(f"Aucune donnée image fournie pour {passenger_id}")
            return None

        try:
            # Créer le répertoire de destination
            image_dir = Path(settings.MEDIA_ROOT) / "db_users" / national_identifier
            image_dir.mkdir(parents=True, exist_ok=True)

            # Vider le répertoire avant de sauvegarder la nouvelle image
            for existing_file in image_dir.glob("*"):
                try:
                    existing_file.unlink()
                    logger.info(f"Fichier supprimé : {existing_file}")
                except Exception as e:
                    logger.error(f"Échec suppression fichier {existing_file}: {str(e)}")

            # Décoder l'image base64
            header, encoded = image_data.split(",", 1)
            file_ext = header.split(";")[0].split("/")[-1].lower()
            image_path = image_dir / f"{passenger_id}.{file_ext}"

            # Sauvegarder la nouvelle image
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(encoded))

            logger.info(f"Image sauvegardée avec succès pour {passenger_id}")
            return str(image_path.relative_to(settings.MEDIA_ROOT))

        except Exception as e:
            logger.error(f"Erreur sauvegarde image {passenger_id}: {str(e)}", exc_info=True)
            return None

    def process_all_passengers(self):
        """Processus complet de récupération des images"""
        try:
            # Authentification
            self.authenticate()

            # Récupération des passagers
            passengers = self.get_passengers()
            results = []

            for passenger in passengers:
                passenger_id = passenger.get('id')
                if not passenger_id:
                    continue

                try:
                    # Récupération des détails
                    details = self.get_passenger_details(passenger_id)

                    # Extraction de l'image
                    other_data = details.get('other', {})
                    images = other_data.get('images', {})
                    image_key = next(
                        (k for k in images.keys() if k.startswith('Image_')), None)
                    image_data = images.get(image_key) if image_key else None
                    identifier = other_data.get('national_identifier',
                                                other_data.get('document_number', {}))

                    # Sauvegarde de l'image
                    image_path = self.save_passenger_image(
                        identifier, passenger_id, image_data) if image_data else None

                    results.append({
                        'passenger_id': passenger_id,
                        'status': 'success',
                        'image_saved': bool(image_path),
                        'image_path': image_path
                    })

                except Exception as e:
                    logger.error(
                        f"Erreur traitement passager {passenger_id}: {str(e)}")
                    results.append({
                        'passenger_id': passenger_id,
                        'status': 'error',
                        'error': str(e)
                    })

            return results

        except Exception as e:
            logger.error(f"Erreur globale du processus: {str(e)}")
            raise
