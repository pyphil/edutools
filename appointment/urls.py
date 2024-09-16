from django.urls import path
from . import views


urlpatterns = [
    path('', views.appointment, name='appointment'),
    path('create_appointment', views.create_appointment, name='create_appointment'),
    path('book_appointment/<int:id>', views.book_appointment, name='book_appointment'),
    path('edit_appointment/<int:id>', views.edit_appointment, name='edit_appointment'),
    path('delete_appointment/<int:id>', views.delete_appointment, name='delete_appointment'),
    path('appointment_admin', views.appointment_admin, name='appointment_admin'),
]
