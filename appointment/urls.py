from django.urls import path
from . import views


urlpatterns = [
    path('', views.appointment, name='appointment'),
    path('create_appointment', views.create_appointment, name='create_appointment'),
    path('book_appointment/<int:id>', views.book_appointment, name='book_appointment'),
]
