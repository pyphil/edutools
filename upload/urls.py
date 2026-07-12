from . import views
from django.urls import path

urlpatterns = [
    path('<str:key>/', views.upload, name='upload'),
    path('laufband/<str:key>/', views.upload_laufband, name='upload_laufband'),
]
