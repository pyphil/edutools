from django.urls import path

from . import views

app_name = 'clubs'

urlpatterns = [
    # public (students, identified by Wahlcode)
    path('', views.index, name='index'),
    path('wahl/', views.choose, name='choose'),
    path('abmelden/', views.student_logout, name='student_logout'),
    # internal
    path('verwaltung/', views.manage, name='manage'),
    path('verwaltung/schueler/', views.manage_students, name='manage_students'),
    path('verwaltung/schueler/<int:pk>/', views.student_edit, name='student_edit'),
    path('verwaltung/ags/', views.manage_clubs, name='manage_clubs'),
    path('verwaltung/import/', views.manage_import, name='import'),
    path('verwaltung/drucken/codes/', views.print_codes, name='print_codes'),
    path('verwaltung/drucken/ags/', views.print_by_club, name='print_by_club'),
    path('verwaltung/drucken/klassen/', views.print_by_group, name='print_by_group'),
]
