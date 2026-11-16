from django.urls import path
from . import views

app_name = 'eduCards'

urlpatterns = [
    path('', views.cards_page_list, name='cards_page_list'),
    # Boards
    path('page/create/', views.create_cards_page, name='create_cards_page'),
    path('page/<int:page_id>/', views.cards_page_detail, name='cards_page_detail'),
    path('page/<int:page_id>/state/', views.cards_page_state, name='cards_page_state'),
    path('page/<int:page_id>/edit/', views.edit_cards_page, name='edit_cards_page'),
    path('page/<int:page_id>/delete/', views.delete_cards_page, name='delete_cards_page'),
    path('page/<int:page_id>/archive/', views.toggle_archive_cards_page, name='toggle_archive_cards_page'),
    path('page/<int:page_id>/duplicate/', views.duplicate_cards_page, name='duplicate_cards_page'),
    path('page/<int:page_id>/share/', views.share_cards_page, name='share_cards_page'),
    path('page/<int:page_id>/qr-tokens/', views.share_cards_page, name='manage_qr_tokens'),
    path('page/<int:page_id>/access/<str:token>/', views.access_page_via_qr, name='access_page_via_qr'),
    # Columns
    path('page/<int:page_id>/category/create/', views.create_category, name='create_category'),
    path('page/<int:page_id>/categories/reorder/', views.reorder_categories, name='reorder_categories'),
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    # Cards
    path('category/<int:category_id>/card/create/', views.create_card, name='create_card'),
    path('page/<int:page_id>/cards/reorder/', views.reorder_cards, name='reorder_cards'),
    path('card/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('card/<int:card_id>/approve/', views.approve_card, name='approve_card'),
    path('card/<int:card_id>/pin/', views.pin_card, name='pin_card'),
    path('card/<int:card_id>/react/', views.react_card, name='react_card'),
    path('card/<int:card_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    # Files
    path('card/<int:card_id>/download/', views.download_attachment, name='download_attachment'),
    path('card/<int:card_id>/attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
]
