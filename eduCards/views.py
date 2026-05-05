import base64
import secrets
from io import BytesIO

import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse
from django.conf import settings
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import CardsPage, Category, Card, CardsPageAccessToken
from .forms import CardsPageForm, CategoryForm, CardForm, CardsPageShareForm


def is_teacher(user):
    return user.is_staff or user.groups.filter(name='teachers').exists()


def get_edu_cards_access_pages(request):
    """Returns dict of accessible page IDs and their access levels"""
    access_pages = request.session.get('edu_cards_access_pages', {})
    if not isinstance(access_pages, dict):
        access_pages = {}
    return access_pages


def grant_edu_cards_page_access(request, page_id, access_level=CardsPageAccessToken.ACCESS_EDIT):
    """Grant access to a page and store the access level"""
    access_pages = request.session.get('edu_cards_access_pages', {})
    if not isinstance(access_pages, dict):
        access_pages = {}
    access_pages[str(page_id)] = access_level
    request.session['edu_cards_access_pages'] = access_pages


def get_qr_access_level(request, page_id):
    """Get QR access level for a page, or None if not accessible"""
    access_pages = request.session.get('edu_cards_access_pages', {})
    return access_pages.get(str(page_id))


def is_page_member(user, cards_page):
    return cards_page.created_by == user or cards_page.shared_with.filter(pk=user.pk).exists()


def can_create_cards(request, cards_page):
    """User can create cards if they belong to the page or have EDIT QR access."""
    if request.user.is_authenticated and is_teacher(request.user):
        return is_page_member(request.user, cards_page)
    access_level = get_qr_access_level(request, cards_page.id)
    return access_level == CardsPageAccessToken.ACCESS_EDIT


def can_view_page(request, cards_page):
    """User can view page if they are page creator, shared teacher, or have any QR access."""
    if request.user.is_authenticated and is_teacher(request.user):
        return is_page_member(request.user, cards_page)
    return cards_page.id in [int(k) for k in request.session.get('edu_cards_access_pages', {}).keys()]


def render_edu_cards(request, template_name, context=None):
    if context is None:
        context = {}
    context.setdefault('user_is_teacher', is_teacher(request.user))
    context.setdefault('edu_cards_access_pages', get_edu_cards_access_pages(request))
    return render(request, template_name, context)


def cards_page_list(request):
    """List all active cards pages accessible to the user"""
    if request.user.is_authenticated and is_teacher(request.user):
        own_pages = CardsPage.objects.filter(
            is_active=True,
            created_by=request.user
        ).order_by('order', 'title')
        shared_pages = CardsPage.objects.filter(
            is_active=True,
            shared_with=request.user
        ).exclude(created_by=request.user).order_by('order', 'title')
        return render_edu_cards(request, 'eduCards/cards_page_list.html', {
            'own_pages': own_pages,
            'shared_pages': shared_pages,
            'cards_pages': CardsPage.objects.none(),
        })

    access_page_ids = [int(k) for k in request.session.get('edu_cards_access_pages', {}).keys()]
    cards_pages = CardsPage.objects.filter(
        is_active=True,
        id__in=access_page_ids
    ).order_by('order', 'title') if access_page_ids else CardsPage.objects.none()
    
    return render_edu_cards(request, 'eduCards/cards_page_list.html', {
        'cards_pages': cards_pages,
    })


def cards_page_detail(request, page_id):
    """Display a cards page with all its categories and cards"""
    cards_page = get_object_or_404(CardsPage, id=page_id, is_active=True)
    
    # Check if user has access to this page
    if not can_view_page(request, cards_page):
        return render(request, 'eduCards/edu_cards_no_access.html', {'cards_page': cards_page})
    
    categories = cards_page.categories.all().order_by('order', 'name').prefetch_related(
        Prefetch('cards', queryset=Card.objects.order_by('order', 'title'))
    )
    
    return render_edu_cards(request, 'eduCards/cards_page_detail.html', {
        'cards_page': cards_page,
        'categories': categories,
        'can_create_cards': can_create_cards(request, cards_page),
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
    
    return render_edu_cards(request, 'eduCards/cards_page_form.html', {
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
    
    return render_edu_cards(request, 'eduCards/cards_page_form.html', {
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
    
    return render_edu_cards(request, 'eduCards/category_form.html', {
        'form': form,
        'cards_page': cards_page,
        'title': _('Create New Category'),
    })


@login_required
@user_passes_test(is_teacher)
def share_cards_page(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    share_form = CardsPageShareForm(
        request.POST if request.method == 'POST' and request.POST.get('share') else None,
        initial={'teachers': cards_page.shared_with.all()}
    )

    if request.method == 'POST':
        if request.POST.get('create_qr'):
            token = secrets.token_urlsafe(18)
            access_level = request.POST.get('access_level', CardsPageAccessToken.ACCESS_EDIT)
            CardsPageAccessToken.objects.create(
                cards_page=cards_page,
                token=token,
                access_level=access_level,
                created_by=request.user,
            )
            return redirect('eduCards:manage_qr_tokens', page_id=page_id)

        if request.POST.get('delete'):
            token_id = request.POST.get('delete')
            token_obj = get_object_or_404(CardsPageAccessToken, id=token_id, cards_page=cards_page)
            token_obj.delete()
            return redirect('eduCards:manage_qr_tokens', page_id=page_id)

        if request.POST.get('share') and share_form.is_valid():
            cards_page.shared_with.set(share_form.cleaned_data['teachers'])
            return redirect('eduCards:manage_qr_tokens', page_id=page_id)

        if request.POST.get('remove_share'):
            teacher_id = request.POST.get('remove_share')
            cards_page.shared_with.remove(teacher_id)
            return redirect('eduCards:manage_qr_tokens', page_id=page_id)

    tokens = CardsPageAccessToken.objects.filter(cards_page=cards_page, is_active=True)
    token_data = []
    for token in tokens:
        url = request.build_absolute_uri(
            reverse('eduCards:access_page_via_qr', kwargs={'page_id': cards_page.id, 'token': token.token})
        )
        qr = qrcode.make(url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        token_data.append({
            'token': token,
            'url': url,
            'qr_base64': base64.b64encode(buffer.getvalue()).decode('utf-8'),
        })

    return render_edu_cards(request, 'eduCards/cards_page_qr_tokens.html', {
        'cards_page': cards_page,
        'token_data': token_data,
        'access_choices': CardsPageAccessToken.ACCESS_CHOICES,
        'share_form': share_form,
        'shared_teachers': cards_page.shared_with.all(),
    })


def access_page_via_qr(request, page_id, token):
    cards_page = get_object_or_404(CardsPage, id=page_id, is_active=True)
    token_obj = get_object_or_404(CardsPageAccessToken, cards_page=cards_page, token=token, is_active=True)
    grant_edu_cards_page_access(request, cards_page.id, token_obj.access_level)
    return redirect('eduCards:cards_page_detail', page_id=cards_page.id)


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
    
    return render_edu_cards(request, 'eduCards/category_form.html', {
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
    
    return render_edu_cards(request, 'eduCards/category_delete.html', {
        'category': category,
    })


def create_card(request, category_id):
    """Create a new card within a category"""
    category = get_object_or_404(Category, id=category_id)
    page = category.cards_page

    if not can_create_cards(request, page):
        if request.user.is_authenticated:
            return render(request, 'eduCards/edu_cards_no_access.html', {'cards_page': page})
        return redirect('eduCards:cards_page_detail', page_id=page.id)

    if request.method == 'POST':
        form = CardForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.category = category
            card.created_by = request.user if request.user.is_authenticated else None
            card.save()
            return redirect('eduCards:cards_page_detail', page_id=page.id)
    else:
        form = CardForm()
    
    return render_edu_cards(request, 'eduCards/card_form.html', {
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
    
    return render_edu_cards(request, 'eduCards/card_form.html', {
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
    
    return render_edu_cards(request, 'eduCards/card_delete.html', {
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

