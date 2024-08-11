from django.urls import path
from . import views
from .views import rate_limit_exceeded_view

urlpatterns = [
    path('', views.home, name='mkr_home'),
    path('karte/', views.karte, name='karte'),
    path('karte_bearbeiten/<int:id>', views.karte_bearbeiten, name='karte_bearbeiten'),
    path('download/<filename>', views.download, name='download'),
    path('lehrplanansicht', views.lehrplanansicht, name='lehrplanansicht'),
    path('images/<filename>', views.get_image, name='get_image'),
    path('rate-limit-exceeded/', rate_limit_exceeded_view, name='rate_limit_exceeded'),
]
