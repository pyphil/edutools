from django.urls import path
from . import views


urlpatterns = [
    path('', views.edutools_home, name='edutools_home'),
    path('dsb', views.dsb, name='dsb'),
    #path('mkr', views.mkr, name='mkr'),
]
