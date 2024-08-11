from django.urls import path
from . import views


urlpatterns = [
    path('select/', views.select, name='userlistSelect'),
    path('entry/', views.entry, name='userlistEntry'),
    path('success/', views.success, name='userlistSuccess'),
]
