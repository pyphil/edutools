from django.urls import path
from . import views


urlpatterns = [
    path('', views.activity, name='activity'),
    path('success/', views.success, name='success'),
    path('activity_lists/', views.activity_lists, name='activity_lists'),
]
