from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services import PIDCheckService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def sync_passenger_images(request):
    """Endpoint pour synchroniser toutes les images des passagers"""
    service = PIDCheckService()
    
    try:
        results = service.process_all_passengers()
        success_count = sum(1 for r in results if r.get('status') == 'success')
        
        return Response({
            "status": "completed",
            "passengers_processed": len(results),
            "images_saved": success_count,
            "details": results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur endpoint sync_passenger_images: {str(e)}")
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def sync_passenger_images(request):
    """Endpoint pour synchroniser toutes les images des passagers"""
    service = PIDCheckService()
    
    try:
        results = service.process_all_passengers()
        success_count = sum(1 for r in results if r.get('status') == 'success')
        
        return Response({
            "status": "completed",
            "passengers_processed": len(results),
            "images_saved": success_count,
            "details": results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur endpoint sync_passenger_images: {str(e)}")
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    