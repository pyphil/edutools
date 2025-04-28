from django.urls import path
from . import views


urlpatterns = [
    path('', views.edutools_home, name='edutools_home'),
    path('dsb', views.dsb, name='dsb'),
    path('userprofiles/', views.userprofiles, name='userprofiles'),
    path('userprofile_details/<int:id>/', views.userprofile_details, name='userprofile_details'),
    path('userprofile_add/', views.userprofile_add, name='userprofile_add'),
    #path('mkr', views.mkr, name='mkr'),
]
