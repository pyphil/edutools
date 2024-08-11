from django.urls import path
from . import views


urlpatterns = [
    path('', views.inventory, name='inventory'),
    path('import/', views.book_import, name='book_import'),
    path('edit/<int:id>/', views.edit, name='edit'),
    path('new/', views.new, name='new'),
    path('delete/<int:id>/', views.delete, name='delete'),
    path('borrow/<int:id>/', views.borrow, name='borrow'),
    path('returnlist/', views.returnlist, name='returnlist'),
    path('return/<int:id>/', views.return_book, name='return_book'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
    path('new_category/', views.new_category, name='new_category'),
]
