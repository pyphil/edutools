from django.urls import path
from . import views


urlpatterns = [
    path('', views.generate_qr_code, name='generate_qr_code'),
    path('qr_codes/<filename>', views.get_qr_image, name='get_qr_image'),
]
