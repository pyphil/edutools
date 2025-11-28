from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse
from django.conf import settings
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from .models import CardsPage, Category, Card
from .forms import CardsPageForm, CategoryForm, CardForm


def is_teacher(user):
    return user.is_staff or user.groups.filter(name='teachers').exists()


def cards_page_list(request):
    """List all active cards pages"""
    cards_pages = CardsPage.objects.filter(is_active=True).order_by('order', 'title')
    return render(request, 'eduCards/cards_page_list.html', {
        'cards_pages': cards_pages,
    })


def cards_page_detail(request, page_id):
    """Display a cards page with all its categories and cards"""
    cards_page = get_object_or_404(CardsPage, id=page_id, is_active=True)
    categories = cards_page.categories.all().order_by('order', 'name').prefetch_related(
        Prefetch('cards', queryset=Card.objects.order_by('order', 'title'))
    )
    
    return render(request, 'eduCards/cards_page_detail.html', {
        'cards_page': cards_page,
        'categories': categories,
    })


@login_required
@user_passes_test(is_teacher)
def create_cards_page(request):
    """Create a new cards page"""
    if request.method == 'POST':
        form = CardsPageForm(request.POST)
        if form.is_valid():
            cards_page = form.save(commit=False)
            cards_page.created_by = request.user
            cards_page.save()
            return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    else:
        form = CardsPageForm()
    
    return render(request, 'eduCards/cards_page_form.html', {
        'form': form,
        'title': _('Create New Cards Page'),
    })


@login_required
@user_passes_test(is_teacher)
def edit_cards_page(request, page_id):
    """Edit an existing cards page"""
    cards_page = get_object_or_404(CardsPage, id=page_id)
    
    if request.method == 'POST':
        form = CardsPageForm(request.POST, instance=cards_page)
        if form.is_valid():
            cards_page = form.save(commit=False)
            cards_page.last_modified_by = request.user
            cards_page.save()
            return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    else:
        form = CardsPageForm(instance=cards_page)
    
    return render(request, 'eduCards/cards_page_form.html', {
        'form': form,
        'cards_page': cards_page,
        'title': _('Edit Cards Page'),
    })


@login_required
@user_passes_test(is_teacher)
def create_category(request, page_id):
    """Create a new category within a cards page"""
    cards_page = get_object_or_404(CardsPage, id=page_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.cards_page = cards_page
            category.save()
            return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    else:
        form = CategoryForm()
    
    return render(request, 'eduCards/category_form.html', {
        'form': form,
        'cards_page': cards_page,
        'title': _('Create New Category'),
    })


@login_required
@user_passes_test(is_teacher)
def edit_category(request, category_id):
    """Edit an existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category.save()
            return redirect('eduCards:cards_page_detail', page_id=category.cards_page.id)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'eduCards/category_form.html', {
        'form': form,
        'cards_page': category.cards_page,
        'category': category,
        'title': _('Edit Category'),
    })


@login_required
@user_passes_test(is_teacher)
def delete_category(request, category_id):
    """Delete a category"""
    category = get_object_or_404(Category, id=category_id)
    cards_page_id = category.cards_page.id
    
    if request.method == 'POST':
        category.delete()
        return redirect('eduCards:cards_page_detail', page_id=cards_page_id)
    
    return render(request, 'eduCards/category_delete.html', {
        'category': category,
    })


@login_required
@user_passes_test(is_teacher)
def create_card(request, category_id):
    """Create a new card within a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CardForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.category = category
            card.created_by = request.user
            card.save()
            return redirect('eduCards:cards_page_detail', page_id=category.cards_page.id)
    else:
        form = CardForm()
    
    return render(request, 'eduCards/card_form.html', {
        'form': form,
        'category': category,
        'title': _('Create New Card'),
    })


@login_required
@user_passes_test(is_teacher)
def edit_card(request, card_id):
    """Edit an existing card"""
    card = get_object_or_404(Card, id=card_id)
    
    if request.method == 'POST':
        form = CardForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            card = form.save(commit=False)
            card.last_modified_by = request.user
            card.save()
            return redirect('eduCards:cards_page_detail', page_id=card.category.cards_page.id)
    else:
        form = CardForm(instance=card)
    
    return render(request, 'eduCards/card_form.html', {
        'form': form,
        'category': card.category,
        'card': card,
        'title': _('Edit Card'),
    })


@login_required
@user_passes_test(is_teacher)
def delete_card(request, card_id):
    """Delete a card"""
    card = get_object_or_404(Card, id=card_id)
    cards_page_id = card.category.cards_page.id
    
    if request.method == 'POST':
        card.delete()
        return redirect('eduCards:cards_page_detail', page_id=cards_page_id)
    
    return render(request, 'eduCards/card_delete.html', {
        'card': card,
    })


@login_required
@user_passes_test(is_teacher)
def download_attachment(request, card_id):
    """Download a card attachment"""
    card = get_object_or_404(Card, id=card_id)
    if card.attachment:
        return FileResponse(
            open(settings.MEDIA_ROOT + '/' + str(card.attachment), 'rb'),
            as_attachment=True,
            filename=card.attachment.name.split('/')[-1]
        )
    return redirect('eduCards:cards_page_detail', page_id=card.category.cards_page.id)

