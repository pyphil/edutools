import base64
import hashlib
import json
import mimetypes
import os
import re
import secrets
from io import BytesIO
from urllib.parse import urlparse, parse_qs

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django.http import FileResponse, Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CardsPageForm, CategoryForm, CardForm, CardsPageShareForm, CommentForm
from .models import (
    BACKGROUND_CSS, CARD_COLOR_CSS, LIGHT_BACKGROUNDS, CardsPage, Category, Card, CardAttachment, CardComment, CardReaction, CardsPageAccessToken,
)

GUEST_ID_KEY = 'edu_cards_guest_id'
GUEST_NAME_KEY = 'edu_cards_guest_name'
ACCESS_KEY = 'edu_cards_access_pages'

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
YOUTUBE_ID = re.compile(r'^[\w-]{11}$')


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def is_teacher(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='teachers').exists())


def get_edu_cards_access_pages(request):
    """Returns dict of page IDs (as strings) the session got QR access to, with access level"""
    access_pages = request.session.get(ACCESS_KEY, {})
    return access_pages if isinstance(access_pages, dict) else {}


def grant_edu_cards_page_access(request, page_id, access_level=CardsPageAccessToken.ACCESS_EDIT):
    access_pages = get_edu_cards_access_pages(request)
    access_pages[str(page_id)] = access_level
    request.session[ACCESS_KEY] = access_pages


def get_qr_access_level(request, page_id):
    return get_edu_cards_access_pages(request).get(str(page_id))


def get_guest_id(request, create=False):
    guest_id = request.session.get(GUEST_ID_KEY, '')
    if not guest_id and create:
        guest_id = secrets.token_hex(16)
        request.session[GUEST_ID_KEY] = guest_id
    return guest_id


def get_viewer_key(request):
    if request.user.is_authenticated:
        return f'u{request.user.pk}'
    return f'g{get_guest_id(request, create=True)}'


def is_page_member(user, cards_page):
    if not is_teacher(user):
        return False
    return cards_page.created_by_id == user.pk or cards_page.shared_with.filter(pk=user.pk).exists()


def is_member(request, cards_page):
    cache = request.__dict__.setdefault('_edu_cards_member_cache', {})
    if cards_page.pk not in cache:
        cache[cards_page.pk] = is_page_member(request.user, cards_page)
    return cache[cards_page.pk]


def can_view_page(request, cards_page):
    if is_member(request, cards_page):
        return True
    return cards_page.is_active and get_qr_access_level(request, cards_page.id) is not None


def can_create_cards(request, cards_page):
    if is_member(request, cards_page):
        return True
    return cards_page.is_active and get_qr_access_level(request, cards_page.id) == CardsPageAccessToken.ACCESS_EDIT


def can_manage_card(request, card):
    """Members manage every card; guests may manage cards they wrote themselves."""
    page = card.category.cards_page
    if is_member(request, page):
        return True
    guest_id = get_guest_id(request)
    return bool(card.guest_key and guest_id and card.guest_key == guest_id and can_create_cards(request, page))


def render_edu_cards(request, template_name, context=None, status=200):
    context = context or {}
    context.setdefault('user_is_teacher', is_teacher(request.user))
    context.setdefault('edu_cards_access_pages', get_edu_cards_access_pages(request))
    return render(request, template_name, context, status=status)


def no_access(request, cards_page=None, message=None):
    return render_edu_cards(request, 'eduCards/edu_cards_no_access.html', {
        'cards_page': cards_page,
        'message': message,
    }, status=403)


def teacher_required(view):
    return login_required(user_passes_test(is_teacher)(view))


def wants_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
        'application/json' in request.headers.get('accept', '')


def safe_next(request, fallback):
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return target
    return fallback


def board_url(page, anchor=None):
    url = reverse('eduCards:cards_page_detail', kwargs={'page_id': page.id})
    return f'{url}#{anchor}' if anchor else url


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------

def youtube_id(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    candidate = None
    if host == 'youtu.be':
        candidate = parsed.path.lstrip('/').split('/')[0]
    elif host in ('youtube.com', 'youtube-nocookie.com', 'music.youtube.com'):
        if parsed.path == '/watch':
            candidate = parse_qs(parsed.query).get('v', [None])[0]
        else:
            parts = parsed.path.strip('/').split('/')
            if len(parts) >= 2 and parts[0] in ('embed', 'shorts', 'live', 'v'):
                candidate = parts[1]
    return candidate if candidate and YOUTUBE_ID.match(candidate) else None


def link_domain(url):
    try:
        return (urlparse(url).hostname or '').removeprefix('www.')
    except ValueError:
        return ''


def file_icon(name):
    extension = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    return {
        'pdf': 'bi-file-earmark-pdf', 'doc': 'bi-file-earmark-word', 'docx': 'bi-file-earmark-word',
        'odt': 'bi-file-earmark-word', 'xls': 'bi-file-earmark-excel', 'xlsx': 'bi-file-earmark-excel',
        'ods': 'bi-file-earmark-excel', 'ppt': 'bi-file-earmark-slides', 'pptx': 'bi-file-earmark-slides',
        'odp': 'bi-file-earmark-slides', 'zip': 'bi-file-earmark-zip', 'txt': 'bi-file-earmark-text',
        'mp3': 'bi-file-earmark-music', 'm4a': 'bi-file-earmark-music', 'mp4': 'bi-file-earmark-play',
    }.get(extension, 'bi-file-earmark')


def card_files(card):
    download = reverse('eduCards:download_attachment', kwargs={'card_id': card.id})
    files = []
    entries = [(a.id, a.file.name) for a in card.attachments.all()]
    if not entries and card.attachment:
        entries = [(None, card.attachment.name)]
    for attachment_id, name in entries:
        query = f'?attachment_id={attachment_id}' if attachment_id else ''
        separator = '&' if query else '?'
        lowered = name.lower()
        kind = 'image' if lowered.endswith(IMAGE_EXTENSIONS) else 'pdf' if lowered.endswith('.pdf') else 'file'
        files.append({
            'id': attachment_id,
            'name': name.rsplit('/', 1)[-1],
            'kind': kind,
            'icon': file_icon(name),
            'download_url': f'{download}{query}',
            'inline_url': f'{download}{query}{separator}inline=1',
        })
    return files


def visible_cards_filter(request, cards_page):
    if is_member(request, cards_page):
        return Q()
    guest_id = get_guest_id(request)
    visible = Q(is_approved=True)
    if guest_id:
        visible |= Q(guest_key=guest_id)
    return visible


def build_board(request, cards_page):
    member = is_member(request, cards_page)
    cards_qs = (
        Card.objects.filter(visible_cards_filter(request, cards_page))
        .select_related('created_by', 'last_modified_by')
        .prefetch_related('attachments', Prefetch('comments', queryset=CardComment.objects.select_related('user')))
        .annotate(num_likes=Count('reactions', distinct=True))
        .order_by('-is_pinned', 'order', 'id')
    )
    categories = list(
        cards_page.categories.order_by('order', 'id').prefetch_related(Prefetch('cards', queryset=cards_qs))
    )
    liked = set(CardReaction.objects.filter(
        card__category__cards_page=cards_page, voter_key=get_viewer_key(request)
    ).values_list('card_id', flat=True))
    guest_id = get_guest_id(request)
    total = 0
    for category in categories:
        category.visible_cards = list(category.cards.all())
        total += len(category.visible_cards)
        for card in category.visible_cards:
            card.liked = card.id in liked
            card.can_manage = member or bool(card.guest_key and card.guest_key == guest_id)
            card.youtube_id = youtube_id(card.link_url)
            card.link_domain = link_domain(card.link_url) if card.link_url else ''
            card.files = card_files(card)
            card.comment_list = list(card.comments.all())
            for comment in card.comment_list:
                comment.can_delete = member or bool(comment.guest_key and comment.guest_key == guest_id)
    return categories, total


def board_version(cards_page):
    cards = Card.objects.filter(category__cards_page=cards_page).aggregate(n=Count('id'), m=Max('last_modified'))
    columns = cards_page.categories.aggregate(n=Count('id'), m=Max('last_modified'))
    comments = CardComment.objects.filter(card__category__cards_page=cards_page).aggregate(n=Count('id'), m=Max('id'))
    reactions = CardReaction.objects.filter(card__category__cards_page=cards_page).aggregate(n=Count('id'), m=Max('id'))
    raw = json.dumps([str(cards_page.last_modified), cards, columns, comments, reactions], default=str, sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def touch_page(cards_page, user=None):
    fields = {'last_modified': timezone.now()}
    if user is not None and user.is_authenticated:
        fields['last_modified_by'] = user
    CardsPage.objects.filter(pk=cards_page.pk).update(**fields)


# ---------------------------------------------------------------------------
# Boards
# ---------------------------------------------------------------------------

EMOJI_SUGGESTIONS = ['📌', '💡', '📚', '🧪', '🌍', '🎨', '🎵', '⚽', '🧮', '💬', '🗳️', '🚀', '🌱', '🏛️', '💻', '❤️']


def render_page_form(request, form, title, cards_page=None):
    switches = ['allow_reactions', 'allow_comments', 'require_approval', 'show_author']
    if cards_page is not None:
        switches.append('is_active')
    return render_edu_cards(request, 'eduCards/cards_page_form.html', {
        'form': form,
        'cards_page': cards_page,
        'title': title,
        'switch_fields': [form[name] for name in switches],
        'emoji_suggestions': EMOJI_SUGGESTIONS,
        'background_css_map': BACKGROUND_CSS,
        'light_backgrounds': sorted(LIGHT_BACKGROUNDS),
    })


def annotate_pages(queryset):
    return queryset.annotate(
        num_cards=Count('categories__cards', distinct=True),
        num_columns=Count('categories', distinct=True),
    ).select_related('created_by').order_by('-last_modified')


def cards_page_list(request):
    query = request.GET.get('q', '').strip()
    if is_teacher(request.user):
        mine = CardsPage.objects.filter(created_by=request.user)
        shared = CardsPage.objects.filter(shared_with=request.user).exclude(created_by=request.user)
        if query:
            search = Q(title__icontains=query) | Q(description__icontains=query)
            mine, shared = mine.filter(search), shared.filter(search)
        archived = annotate_pages((mine | shared).filter(is_active=False).distinct())
        return render_edu_cards(request, 'eduCards/cards_page_list.html', {
            'own_pages': annotate_pages(mine.filter(is_active=True)),
            'shared_pages': annotate_pages(shared.filter(is_active=True)),
            'archived_pages': archived,
            'cards_pages': CardsPage.objects.none(),
            'query': query,
        })

    access_page_ids = [int(k) for k in get_edu_cards_access_pages(request).keys() if str(k).isdigit()]
    cards_pages = annotate_pages(CardsPage.objects.filter(is_active=True, id__in=access_page_ids))
    return render_edu_cards(request, 'eduCards/cards_page_list.html', {
        'cards_pages': cards_pages,
        'query': query,
    })


def cards_page_detail(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not cards_page.is_active and not is_member(request, cards_page):
        raise Http404
    if not can_view_page(request, cards_page):
        return render_edu_cards(request, 'eduCards/edu_cards_no_access.html', {'cards_page': cards_page})

    categories, total = build_board(request, cards_page)
    member = is_member(request, cards_page)
    context = {
        'cards_page': cards_page,
        'categories': categories,
        'total_cards': total,
        'is_member': member,
        'can_create_cards': can_create_cards(request, cards_page),
        'can_comment': cards_page.allow_comments and can_create_cards(request, cards_page),
        'pending_count': sum(1 for c in categories for card in c.visible_cards if not card.is_approved) if member else 0,
        'board_version': board_version(cards_page),
        'guest_name': request.session.get(GUEST_NAME_KEY, ''),
        'access_level': get_qr_access_level(request, cards_page.id),
    }
    if request.GET.get('partial') == '1':
        return render_edu_cards(request, 'eduCards/_board.html', context)
    return render_edu_cards(request, 'eduCards/cards_page_detail.html', context)


def cards_page_state(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not can_view_page(request, cards_page):
        return JsonResponse({'error': 'forbidden'}, status=403)
    return JsonResponse({'version': board_version(cards_page)})


@teacher_required
def create_cards_page(request):
    form = CardsPageForm(request.POST or None, with_template=True)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            cards_page = form.save(commit=False)
            cards_page.created_by = request.user
            cards_page.icon = cards_page.icon or '📌'
            cards_page.save()
            for index, (name, color) in enumerate(form.template_columns()):
                Category.objects.create(cards_page=cards_page, name=name, color=color, order=index)
        messages.success(request, 'Das Board wurde erstellt.')
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_page_form(request, form, 'Neues Board erstellen')


@teacher_required
def edit_cards_page(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return no_access(request, cards_page)
    form = CardsPageForm(request.POST or None, instance=cards_page)
    if request.method == 'POST' and form.is_valid():
        cards_page = form.save(commit=False)
        cards_page.icon = cards_page.icon or '📌'
        cards_page.last_modified_by = request.user
        cards_page.save()
        messages.success(request, 'Die Einstellungen wurden gespeichert.')
        if not cards_page.is_active:
            return redirect('eduCards:cards_page_list')
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_page_form(request, form, 'Board-Einstellungen', cards_page)


@teacher_required
def delete_cards_page(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if cards_page.created_by_id != request.user.pk:
        return no_access(request, cards_page, 'Nur die Ersteller:in kann ein Board endgültig löschen.')
    if request.method == 'POST':
        title = cards_page.title
        cards_page.delete()
        messages.success(request, f'Das Board „{title}“ wurde gelöscht.')
        return redirect('eduCards:cards_page_list')
    return render_edu_cards(request, 'eduCards/confirm_delete.html', {
        'cards_page': cards_page,
        'object_label': f'das Board „{cards_page.title}“',
        'details': 'Alle Spalten, Beiträge, Kommentare und Freigabe-Codes werden ebenfalls gelöscht.',
        'cancel_url': board_url(cards_page),
    })


@teacher_required
@require_POST
def toggle_archive_cards_page(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return no_access(request, cards_page)
    cards_page.is_active = not cards_page.is_active
    cards_page.last_modified_by = request.user
    cards_page.save()
    messages.success(request, 'Board wiederhergestellt.' if cards_page.is_active else 'Board archiviert.')
    return redirect(safe_next(request, reverse('eduCards:cards_page_list')))


@teacher_required
@require_POST
def duplicate_cards_page(request, page_id):
    source = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, source):
        return no_access(request, source)
    with transaction.atomic():
        copy = CardsPage.objects.create(
            title=f'Kopie von {source.title}'[:200], description=source.description, icon=source.icon,
            layout=source.layout, background=source.background, allow_comments=source.allow_comments,
            allow_reactions=source.allow_reactions, require_approval=source.require_approval,
            show_author=source.show_author, created_by=request.user,
        )
        for category in source.categories.order_by('order', 'id'):
            new_category = Category.objects.create(
                cards_page=copy, name=category.name, description=category.description,
                color=category.color, order=category.order,
            )
            for card in category.cards.filter(is_approved=True).order_by('order', 'id'):
                attachments = list(card.attachments.all())
                card.pk = None
                card.id = None
                card.category = new_category
                card.guest_key = ''
                card.last_modified_by = None
                card.save()
                for attachment in attachments:
                    CardAttachment.objects.create(card=card, file=attachment.file.name)
    messages.success(request, 'Das Board wurde dupliziert. Kommentare, Likes und Freigabe-Codes wurden nicht übernommen.')
    return redirect('eduCards:cards_page_detail', page_id=copy.id)


@teacher_required
def share_cards_page(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return no_access(request, cards_page)
    manage_url = reverse('eduCards:manage_qr_tokens', kwargs={'page_id': page_id})
    share_form = CardsPageShareForm(
        request.POST if request.method == 'POST' and request.POST.get('share') else None,
        initial={'teachers': cards_page.shared_with.all()}
    )
    share_form.fields['teachers'].queryset = share_form.fields['teachers'].queryset.exclude(pk=cards_page.created_by_id)

    if request.method == 'POST':
        if request.POST.get('create_qr'):
            access_level = request.POST.get('access_level', CardsPageAccessToken.ACCESS_EDIT)
            if access_level not in dict(CardsPageAccessToken.ACCESS_CHOICES):
                access_level = CardsPageAccessToken.ACCESS_EDIT
            CardsPageAccessToken.objects.create(
                cards_page=cards_page, token=secrets.token_urlsafe(18),
                access_level=access_level, created_by=request.user,
            )
            messages.success(request, 'Ein neuer Zugangscode wurde erstellt.')
            return redirect(manage_url)

        if request.POST.get('delete'):
            token_obj = get_object_or_404(CardsPageAccessToken, id=request.POST.get('delete'), cards_page=cards_page)
            token_obj.delete()
            messages.success(request, 'Der Zugangscode wurde gelöscht. Der Link funktioniert nicht mehr.')
            return redirect(manage_url)

        if request.POST.get('share') and share_form.is_valid():
            cards_page.shared_with.set(share_form.cleaned_data['teachers'])
            messages.success(request, 'Die Freigabe für Lehrkräfte wurde gespeichert.')
            return redirect(manage_url)

        if request.POST.get('remove_share'):
            cards_page.shared_with.remove(request.POST.get('remove_share'))
            return redirect(manage_url)

    token_data = []
    for token in CardsPageAccessToken.objects.filter(cards_page=cards_page, is_active=True):
        url = request.build_absolute_uri(
            reverse('eduCards:access_page_via_qr', kwargs={'page_id': cards_page.id, 'token': token.token})
        )
        buffer = BytesIO()
        qrcode.make(url, border=2).save(buffer, format='PNG')
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


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

COLUMN_COLORS = ['#e03131', '#f76707', '#f59f00', '#2f9e44', '#0ca678', '#1c7ed6', '#4f46e5', '#ae3ec9', '#d6336c', '#868e96']

@teacher_required
def create_category(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return no_access(request, cards_page)
    form = CategoryForm(
        request.POST or None, cards_page=cards_page,
        initial={'color': COLUMN_COLORS[cards_page.categories.count() % len(COLUMN_COLORS)]},
    )
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.cards_page = cards_page
        category.order = (cards_page.categories.aggregate(m=Max('order'))['m'] or 0) + 1
        category.save()
        touch_page(cards_page, request.user)
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_edu_cards(request, 'eduCards/category_form.html', {
        'form': form,
        'cards_page': cards_page,
        'title': 'Neue Spalte',
        'column_colors': COLUMN_COLORS,
    })


@teacher_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if not is_member(request, category.cards_page):
        return no_access(request, category.cards_page)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('eduCards:cards_page_detail', page_id=category.cards_page.id)
    return render_edu_cards(request, 'eduCards/category_form.html', {
        'form': form,
        'cards_page': category.cards_page,
        'category': category,
        'title': 'Spalte bearbeiten',
        'column_colors': COLUMN_COLORS,
    })


@teacher_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    cards_page = category.cards_page
    if not is_member(request, cards_page):
        return no_access(request, cards_page)
    if request.method == 'POST':
        category.delete()
        touch_page(cards_page, request.user)
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_edu_cards(request, 'eduCards/confirm_delete.html', {
        'cards_page': cards_page,
        'object_label': f'die Spalte „{category.name}“',
        'details': f'{category.cards.count()} Beitrag/Beiträge in dieser Spalte werden ebenfalls gelöscht.',
        'cancel_url': board_url(cards_page),
    })


@require_POST
def reorder_categories(request, page_id):
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        ids = [int(i) for i in json.loads(request.body).get('category_ids', [])]
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'error': 'invalid'}, status=400)
    valid = set(cards_page.categories.values_list('id', flat=True))
    now = timezone.now()
    with transaction.atomic():
        for index, category_id in enumerate(i for i in ids if i in valid):
            Category.objects.filter(pk=category_id).update(order=index, last_modified=now)
    return JsonResponse({'ok': True, 'version': board_version(cards_page)})


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def _save_card(request, form, cards_page, card, is_new, fallback_category):
    member = is_member(request, cards_page)
    card.category = form.cleaned_data.get('category') or fallback_category
    if card.category.cards_page_id != cards_page.id:
        raise Http404
    if is_new:
        card.order = (card.category.cards.aggregate(m=Max('order'))['m'] or 0) + 1
        if request.user.is_authenticated:
            card.created_by = request.user
        if not member:
            card.guest_key = get_guest_id(request, create=True)
    elif request.user.is_authenticated:
        card.last_modified_by = request.user
    if not member:
        name = (form.cleaned_data.get('author_name') or '').strip()
        card.author_name = name
        request.session[GUEST_NAME_KEY] = name
        card.is_approved = not cards_page.require_approval
    card.save()
    for uploaded_file in form.cleaned_data.get('attachments', []):
        CardAttachment.objects.create(card=card, file=uploaded_file)
    touch_page(cards_page, request.user)
    if not card.is_approved:
        messages.info(request, 'Danke! Dein Beitrag wird sichtbar, sobald eine Lehrkraft ihn freigegeben hat.')


def create_card(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    cards_page = category.cards_page
    if not can_create_cards(request, cards_page):
        if request.user.is_authenticated and not get_qr_access_level(request, cards_page.id):
            return no_access(request, cards_page)
        messages.warning(request, 'Du darfst auf diesem Board keine Beiträge erstellen.')
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)

    member = is_member(request, cards_page)
    form = CardForm(
        request.POST or None, request.FILES or None,
        cards_page=cards_page, show_author_field=not member,
        initial={'category': category, 'author_name': request.session.get(GUEST_NAME_KEY, '')},
    )
    if request.method == 'POST' and form.is_valid():
        card = form.save(commit=False)
        _save_card(request, form, cards_page, card, is_new=True, fallback_category=category)
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_edu_cards(request, 'eduCards/card_form.html', {
        'form': form,
        'category': category,
        'cards_page': cards_page,
        'title': 'Neuer Beitrag',
        'card_color_css': CARD_COLOR_CSS,
    })


def edit_card(request, card_id):
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    cards_page = card.category.cards_page
    if not can_manage_card(request, card):
        if not request.user.is_authenticated and get_qr_access_level(request, cards_page.id) is None:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return no_access(request, cards_page, 'Du kannst nur deine eigenen Beiträge bearbeiten.')

    member = is_member(request, cards_page)
    original_category = card.category
    form = CardForm(
        request.POST or None, request.FILES or None, instance=card,
        cards_page=cards_page, show_author_field=not member,
    )
    if request.method == 'POST' and form.is_valid():
        card = form.save(commit=False)
        _save_card(request, form, cards_page, card, is_new=False, fallback_category=original_category)
        return redirect(board_url(cards_page, f'card-{card.id}'))
    return render_edu_cards(request, 'eduCards/card_form.html', {
        'form': form,
        'category': card.category,
        'cards_page': cards_page,
        'card': card,
        'files': card_files(card),
        'title': 'Beitrag bearbeiten',
        'card_color_css': CARD_COLOR_CSS,
    })


def delete_card(request, card_id):
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    cards_page = card.category.cards_page
    if not can_manage_card(request, card):
        if not request.user.is_authenticated and get_qr_access_level(request, cards_page.id) is None:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return no_access(request, cards_page, 'Du kannst nur deine eigenen Beiträge löschen.')
    if request.method == 'POST':
        card.delete()
        touch_page(cards_page, request.user)
        if wants_json(request):
            return JsonResponse({'ok': True})
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    return render_edu_cards(request, 'eduCards/confirm_delete.html', {
        'cards_page': cards_page,
        'object_label': f'den Beitrag „{card.title}“',
        'details': 'Kommentare, Likes und Dateien des Beitrags werden ebenfalls gelöscht.',
        'cancel_url': board_url(cards_page, f'card-{card.id}'),
    })


@require_POST
def reorder_cards(request, page_id):
    """Persist drag & drop: receives the complete ordered card list of one column."""
    cards_page = get_object_or_404(CardsPage, id=page_id)
    if not is_member(request, cards_page):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        payload = json.loads(request.body)
        category = get_object_or_404(Category, id=int(payload.get('category_id')), cards_page=cards_page)
        ids = [int(i) for i in payload.get('card_ids', [])]
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'error': 'invalid'}, status=400)
    valid = set(Card.objects.filter(category__cards_page=cards_page, id__in=ids).values_list('id', flat=True))
    now = timezone.now()
    with transaction.atomic():
        for index, card_id in enumerate(i for i in ids if i in valid):
            Card.objects.filter(pk=card_id).update(category=category, order=index, last_modified=now)
    return JsonResponse({'ok': True, 'version': board_version(cards_page)})


def _member_card_action(request, card_id):
    if request.method != 'POST':
        return None, HttpResponseNotAllowed(['POST'])
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    if not is_member(request, card.category.cards_page):
        return None, no_access(request, card.category.cards_page)
    return card, None


def approve_card(request, card_id):
    card, error = _member_card_action(request, card_id)
    if error:
        return error
    card.is_approved = True
    card.save(update_fields=['is_approved', 'last_modified'])
    if wants_json(request):
        return JsonResponse({'ok': True})
    return redirect(board_url(card.category.cards_page, f'card-{card.id}'))


def pin_card(request, card_id):
    card, error = _member_card_action(request, card_id)
    if error:
        return error
    card.is_pinned = not card.is_pinned
    card.save(update_fields=['is_pinned', 'last_modified'])
    if wants_json(request):
        return JsonResponse({'ok': True, 'pinned': card.is_pinned})
    return redirect(board_url(card.category.cards_page, f'card-{card.id}'))


@require_POST
def react_card(request, card_id):
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    cards_page = card.category.cards_page
    if not cards_page.allow_reactions or not can_view_page(request, cards_page):
        return JsonResponse({'error': 'forbidden'}, status=403)
    key = get_viewer_key(request)
    reaction, created = CardReaction.objects.get_or_create(card=card, voter_key=key)
    if not created:
        reaction.delete()
    return JsonResponse({'liked': created, 'count': card.reactions.count()})


@require_POST
def add_comment(request, card_id):
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    cards_page = card.category.cards_page
    if not cards_page.allow_comments or not can_create_cards(request, cards_page):
        return no_access(request, cards_page, 'Auf diesem Board kannst du keine Kommentare schreiben.')
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = CardComment(card=card, text=form.cleaned_data['text'].strip())
        if request.user.is_authenticated:
            comment.user = request.user
        if not is_member(request, cards_page):
            comment.guest_key = get_guest_id(request, create=True)
            name = form.cleaned_data.get('author_name', '').strip() or request.session.get(GUEST_NAME_KEY, '')
            comment.author_name = name
            if name:
                request.session[GUEST_NAME_KEY] = name
        if comment.text:
            comment.save()
            touch_page(cards_page)
    return redirect(board_url(cards_page, f'card-{card.id}'))


@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(CardComment.objects.select_related('card__category__cards_page'), id=comment_id)
    cards_page = comment.card.category.cards_page
    guest_id = get_guest_id(request)
    if not (is_member(request, cards_page) or (comment.guest_key and comment.guest_key == guest_id)):
        return no_access(request, cards_page)
    card_id = comment.card_id
    comment.delete()
    touch_page(cards_page)
    return redirect(board_url(cards_page, f'card-{card_id}'))


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

@require_POST
def delete_attachment(request, card_id, attachment_id):
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    attachment = get_object_or_404(CardAttachment, id=attachment_id, card=card)
    cards_page = card.category.cards_page
    if not can_manage_card(request, card):
        return redirect('eduCards:cards_page_detail', page_id=cards_page.id)
    attachment.delete()
    touch_page(cards_page, request.user)
    return redirect(safe_next(request, board_url(cards_page, f'card-{card.id}')))


def download_attachment(request, card_id):
    """Serve a card attachment for download or inline preview."""
    card = get_object_or_404(Card.objects.select_related('category__cards_page'), id=card_id)
    if not can_view_page(request, card.category.cards_page):
        return redirect('eduCards:cards_page_detail', page_id=card.category.cards_page.id)

    attachment_id = request.GET.get('attachment_id')
    if attachment_id:
        file_field = get_object_or_404(CardAttachment, id=attachment_id, card=card).file
    elif card.attachment:
        file_field = card.attachment
    else:
        raise Http404

    media_root = os.path.realpath(settings.MEDIA_ROOT)
    file_path = os.path.realpath(os.path.join(media_root, str(file_field)))
    if not file_path.startswith(media_root + os.sep) or not os.path.isfile(file_path):
        raise Http404

    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'
    # Only images and PDFs may be shown inline; everything else is a download.
    inline = request.GET.get('inline', '0') == '1' and (
        content_type.startswith('image/') and content_type != 'image/svg+xml' or content_type == 'application/pdf'
    )
    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=not inline,
        filename=os.path.basename(file_path),
        content_type=content_type,
    )
    response['Cache-Control'] = 'private, max-age=300'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
