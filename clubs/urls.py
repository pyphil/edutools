from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.index, name='index'),
    path('choose/', views.choose_club, name='choose'),
    path('manage/', views.manage_assignments, name='manage'),
]
