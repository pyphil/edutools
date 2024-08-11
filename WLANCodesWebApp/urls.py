from django.urls import path
from . import views

urlpatterns = [
    path('', views.codes, name='codes'),
    path('new_student/', views.new_student, name='new_student'),
    path('edit_student/<int:id>', views.edit_student, name='edit_student'),
    path('delete_student/<id>', views.delete_student, name='delete_student'),
    path('students/', views.students, name='students'),
    path('students/<int:alert>', views.students, name='students'),
    path('student_import/', views.student_import, name='student_import'),
    path('codedeletion/', views.codedeletion, name='codedeletion'),
    path('rate-limit-exceeded/', views.rate_limit_exceeded_view, name='rate_limit_exceeded'),
]
