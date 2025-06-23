"""
URL configuration for backend_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from face_recognition.views import *
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.static import static
from api.views import *

urlpatterns = [
    path('register_face/', csrf_exempt(register_face),
         name='regiter_face_api'),
    path('update_face/', csrf_exempt(update_face),
         name='update_face_api'),
    path('process_pending_users/', csrf_exempt(process_pending_users),
         name='process_pending_users_api'),
     path('load_process_images/', csrf_exempt(sync_and_process_all),
         name='load_process_images_api'),
    path('list_pending_users/', csrf_exempt(list_pending_users),
         name='list_pending_users_api'),
    path('sync-images/', csrf_exempt(sync_passenger_images),
         name='sync_user_images'),
    path('search_face/', csrf_exempt(verify_face_topn),
         name='search_face_api'),
    path('user_exists/', csrf_exempt(user_exists),
         name='user_exists_api'),
    path('delete_user', csrf_exempt(delete_user),
         name='delete_user_api'),
    path('clear_database/', csrf_exempt(clear_database),
         name='clear_database_api'),
    path('list_users/', csrf_exempt(list_users),
         name='list_users_api'),
    path('statitistique/', csrf_exempt(face_stats), name='face_statitistique')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
