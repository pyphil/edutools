from django.urls import path
from . import views

app_name = 'eduCards'

urlpatterns = [
    path('', views.cards_page_list, name='cards_page_list'),
    path('page/<int:page_id>/', views.cards_page_detail, name='cards_page_detail'),
    path('page/create/', views.create_cards_page, name='create_cards_page'),
    path('page/<int:page_id>/edit/', views.edit_cards_page, name='edit_cards_page'),
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('page/<int:page_id>/category/create/', views.create_category, name='create_category'),
    path('card/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('category/<int:category_id>/card/create/', views.create_card, name='create_card'),
    path('card/<int:card_id>/download/', views.download_attachment, name='download_attachment'),
]

