from django.urls import path
from . import views


urlpatterns = [
    path('dsb2/<str:key>/', views.dsb2, name="dsb2"),
    path('dsb1/<str:key>/', views.dsb1, name="dsb1"),
    path('dsb1_sus/<str:key>/', views.dsb1_sus, name="dsb1_sus"),
    path('dsb2_sus/<str:key>/', views.dsb2_sus, name="dsb2_sus"),
    path('dsb2_info/<str:key>/', views.dsb2_info, name="dsb2_info"),
    path('dsb1_info/<str:key>/', views.dsb1_info, name="dsb1_info"),
    path('dsb_kplan/<str:key>/', views.dsb_kplan, name="dsb_kplan"),
    path('dsb_terminplan/<str:key>/', views.dsb_terminplan, name="dsb_terminplan"),
    path('media/<str:key>/<str:subfolder>/<path:filename>', views.dsb_media, name="dsb_media"),
]
