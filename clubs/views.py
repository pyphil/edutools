from collections import OrderedDict

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .forms import (ChoiceForm, ClubForm, ClubSettingForm, StudentForm,
                    StudentImportForm, TokenForm)
from .models import Club, ClubChoice, ClubSetting, Student
from .services import (auto_assign, decode_upload, group_sort_key,
                       import_students, sorted_groups, student_sort_key)

SESSION_KEY = 'clubs_student_id'


def is_clubs_admin(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='clubs_admin').exists())


def clubs_admin_required(view):
    return login_required(user_passes_test(is_clubs_admin)(view))


# ---------------------------------------------------------------------------
# Public part: Wahlcode entry and choice
# ---------------------------------------------------------------------------

def _session_student(request):
    student_id = request.session.get(SESSION_KEY)
    if not student_id:
        return None
    return Student.objects.filter(pk=student_id).select_related('assigned').first()


@ratelimit(key='ip', rate='120/m', method='POST', block=True)
def index(request):
    setting = ClubSetting.get()
    if request.method == 'POST':
        form = TokenForm(request.POST)
        if form.is_valid():
            request.session[SESSION_KEY] = form.student.pk
            return redirect('clubs:choose')
    else:
        form = TokenForm(initial={'code': request.GET.get('code', '')})
    return render(request, 'clubs/index.html', {
        'setting': setting,
        'form': form,
        'session_student': _session_student(request),
        'is_admin': is_clubs_admin(request.user),
    })


def choose(request):
    student = _session_student(request)
    if student is None:
        return redirect('clubs:index')
    setting = ClubSetting.get()
    clubs = Club.objects.all()
    choice = student.get_choice()

    if request.method == 'POST':
        if not setting.voting_open:
            messages.error(request, 'Die Wahl ist geschlossen. Änderungen sind nicht mehr möglich.')
            return redirect('clubs:choose')
        form = ChoiceForm(request.POST, clubs=clubs)
        if form.is_valid():
            if choice is None:
                choice = ClubChoice(student=student)
            choice.choice1 = form.cleaned_data.get('choice1')
            choice.choice2 = form.cleaned_data.get('choice2')
            choice.choice3 = form.cleaned_data.get('choice3')
            choice.save()
            messages.success(request, 'Deine Wahl wurde gespeichert. Du kannst sie bis zum Ende der Wahl noch ändern.')
            return redirect('clubs:choose')
    else:
        initial = {}
        if choice is not None:
            initial = {'choice1': choice.choice1_id, 'choice2': choice.choice2_id, 'choice3': choice.choice3_id}
        form = ChoiceForm(initial=initial, clubs=clubs)

    return render(request, 'clubs/choose.html', {
        'setting': setting,
        'student': student,
        'choice': choice,
        'form': form,
        'clubs': clubs,
    })


@require_POST
def student_logout(request):
    request.session.pop(SESSION_KEY, None)
    messages.info(request, 'Du wurdest abgemeldet.')
    return redirect('clubs:index')


# ---------------------------------------------------------------------------
# Internal part
# ---------------------------------------------------------------------------

def _clubs_with_counts():
    clubs = list(Club.objects.annotate(
        n_assigned=Count('assigned_students', distinct=True),
        n_wish1=Count('first_choices', distinct=True),
        n_wish2=Count('second_choices', distinct=True),
        n_wish3=Count('third_choices', distinct=True),
    ))
    for club in clubs:
        club.is_over = bool(club.max_size and club.n_assigned > club.max_size)
        club.is_full = bool(club.max_size and club.n_assigned == club.max_size)
        club.demand_over = bool(club.max_size and club.n_wish1 > club.max_size)
        club.free = (club.max_size - club.n_assigned) if club.max_size else None
        club.over_by = -club.free if club.is_over else 0
        club.percent = min(100, round(club.n_assigned * 100 / club.max_size)) if club.max_size else 0
        if club.max_size:
            club.label = f'{club.name} ({club.n_assigned}/{club.max_size})'
        else:
            club.label = f'{club.name} ({club.n_assigned})'
    return clubs


def _decorate(students):
    """Attach wishes and rank of the assignment to each student for templates."""
    for s in students:
        choice = s.get_choice()
        s.wishes = [choice.choice1, choice.choice2, choice.choice3] if choice else []
        s.has_voted = choice is not None
        s.rank = s.assigned_rank()
    return students


def _student_queryset():
    return Student.objects.select_related(
        'assigned', 'choice', 'choice__choice1', 'choice__choice2', 'choice__choice3',
    )


@clubs_admin_required
def manage(request):
    setting = ClubSetting.get()
    settings_form = ClubSettingForm(instance=setting)
    unplaced = None

    if request.method == 'POST':
        if 'save_settings' in request.POST:
            settings_form = ClubSettingForm(request.POST, instance=setting)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, 'Einstellungen gespeichert.')
                return redirect('clubs:manage')
        elif 'auto_assign' in request.POST:
            result = auto_assign(reset=bool(request.POST.get('reset')))
            request.session['clubs_unplaced'] = [s.pk for s in result.unplaced]
            if result.unplaced:
                messages.warning(
                    request,
                    f'{result.assigned} Schüler:innen zugeordnet. {len(result.unplaced)} konnten wegen voller AGs '
                    'keinem ihrer Wünsche zugeordnet werden – bitte manuell zuordnen.',
                )
            else:
                messages.success(request, f'{result.assigned} Schüler:innen zugeordnet.')
            return redirect('clubs:manage')

    unplaced_ids = request.session.pop('clubs_unplaced', None)
    if unplaced_ids:
        unplaced = sorted(
            _student_queryset().filter(pk__in=unplaced_ids, assigned__isnull=True), key=student_sort_key,
        )

    clubs = _clubs_with_counts()
    total = Student.objects.count()
    voted = ClubChoice.objects.count()
    assigned = Student.objects.filter(assigned__isnull=False).count()
    waiting = Student.objects.filter(choice__isnull=False, assigned__isnull=True).count()
    capacity = sum(c.max_size for c in clubs if c.max_size)
    unlimited = any(not c.max_size for c in clubs)

    groups = list(
        Student.objects.values('group').annotate(
            total=Count('id'),
            voted=Count('choice'),
            assigned=Count('assigned'),
        )
    )
    groups.sort(key=lambda g: group_sort_key(g['group']))
    for g in groups:
        g['percent'] = round(g['voted'] * 100 / g['total']) if g['total'] else 0

    return render(request, 'clubs/manage_overview.html', {
        'nav': 'overview',
        'setting': setting,
        'settings_form': settings_form,
        'clubs': clubs,
        'total': total,
        'voted': voted,
        'not_voted': total - voted,
        'assigned': assigned,
        'waiting': waiting,
        'capacity': capacity,
        'unlimited': unlimited,
        'groups': groups,
        'unplaced': _decorate(unplaced) if unplaced else None,
        'over_clubs': [c for c in clubs if c.is_over],
    })


STATUS_FILTERS = OrderedDict([
    ('', 'alle'),
    ('not_voted', 'noch nicht gewählt'),
    ('voted', 'gewählt'),
    ('unassigned', 'gewählt, aber noch nicht zugeordnet'),
    ('assigned', 'zugeordnet'),
    ('not_wish', 'zugeordnet, aber nicht nach Wunsch'),
])


@clubs_admin_required
def manage_students(request):
    if request.method == 'POST':
        if 'add_student' in request.POST:
            add_form = StudentForm(request.POST, prefix='new')
            if add_form.is_valid():
                student = add_form.save()
                messages.success(request, f'{student.full_name} angelegt. Wahlcode: {student.display_token}')
            else:
                messages.error(request, 'Bitte Vor- und Nachnamen angeben.')
            return redirect(request.get_full_path())

        if 'save_assignments' in request.POST:
            valid_clubs = set(Club.objects.values_list('id', flat=True))
            wanted = {}
            for key, value in request.POST.items():
                if not key.startswith('assign-'):
                    continue
                try:
                    sid = int(key.split('-', 1)[1])
                    cid = int(value) if value else None
                except ValueError:
                    continue
                if cid is not None and cid not in valid_clubs:
                    continue
                wanted[sid] = cid
            changed = []
            for student in Student.objects.filter(pk__in=wanted.keys()):
                if student.assigned_id != wanted[student.pk]:
                    student.assigned_id = wanted[student.pk]
                    changed.append(student)
            Student.objects.bulk_update(changed, ['assigned'])
            messages.success(request, f'{len(changed)} Zuordnung(en) geändert.')
            return redirect(request.get_full_path())

    group = request.GET.get('klasse', '')
    club_filter = request.GET.get('ag', '')
    status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    students = _student_queryset()
    if group:
        students = students.filter(group=group)
    if club_filter == 'none':
        students = students.filter(assigned__isnull=True)
    elif club_filter.isdigit():
        students = students.filter(assigned_id=int(club_filter))
    if status == 'not_voted':
        students = students.filter(choice__isnull=True)
    elif status == 'voted':
        students = students.filter(choice__isnull=False)
    elif status == 'unassigned':
        students = students.filter(choice__isnull=False, assigned__isnull=True)
    elif status in ('assigned', 'not_wish'):
        students = students.filter(assigned__isnull=False)
    if query:
        students = students.filter(Q(last_name__icontains=query) | Q(first_name__icontains=query))

    students = _decorate(sorted(students, key=student_sort_key))
    if status == 'not_wish':
        students = [s for s in students if s.rank is None]

    return render(request, 'clubs/manage_students.html', {
        'nav': 'students',
        'students': students,
        'clubs': _clubs_with_counts(),
        'groups': sorted_groups(Student.objects.values_list('group', flat=True)),
        'status_filters': STATUS_FILTERS,
        'current': {'klasse': group, 'ag': club_filter, 'status': status, 'q': query},
        'add_form': StudentForm(prefix='new'),
        'total_count': Student.objects.count(),
    })


@clubs_admin_required
def student_edit(request, pk):
    student = get_object_or_404(_student_queryset(), pk=pk)
    form = StudentForm(instance=student)
    back = request.GET.get('next') or reverse('clubs:manage_students')
    if not back.startswith('/'):
        back = reverse('clubs:manage_students')

    if request.method == 'POST':
        if 'delete' in request.POST:
            name = student.full_name
            student.delete()
            messages.success(request, f'{name} wurde gelöscht.')
            return redirect(back)
        if 'new_token' in request.POST:
            student.regenerate_token()
            messages.success(request, f'Neuer Wahlcode für {student.full_name}: {student.display_token}. '
                                      'Der alte Code ist ungültig.')
            return redirect(request.get_full_path())
        if 'reset_choice' in request.POST:
            ClubChoice.objects.filter(student=student).delete()
            messages.success(request, f'Die Wahl von {student.full_name} wurde zurückgesetzt.')
            return redirect(request.get_full_path())
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gespeichert.')
            return redirect(back)

    return render(request, 'clubs/manage_student_edit.html', {
        'nav': 'students',
        'student': _decorate([student])[0],
        'form': form,
        'back': back,
    })


@clubs_admin_required
def manage_clubs(request):
    new_form = ClubForm(prefix='new')
    if request.method == 'POST':
        if 'add_club' in request.POST:
            new_form = ClubForm(request.POST, prefix='new')
            if new_form.is_valid():
                club = new_form.save()
                messages.success(request, f'AG „{club.name}“ angelegt.')
                return redirect('clubs:manage_clubs')
        elif 'save_club' in request.POST or 'delete_club' in request.POST:
            club = get_object_or_404(Club, pk=request.POST.get('club_id'))
            if 'delete_club' in request.POST:
                club.delete()
                messages.success(request, f'AG „{club.name}“ gelöscht.')
                return redirect('clubs:manage_clubs')
            form = ClubForm(request.POST, instance=club, prefix=f'club{club.pk}')
            if form.is_valid():
                form.save()
                messages.success(request, f'AG „{club.name}“ gespeichert.')
                return redirect('clubs:manage_clubs')
            messages.error(request, 'Bitte die Eingaben prüfen.')

    clubs = _clubs_with_counts()
    for club in clubs:
        club.form = ClubForm(instance=club, prefix=f'club{club.pk}')
    return render(request, 'clubs/manage_clubs.html', {
        'nav': 'clubs',
        'clubs': clubs,
        'new_form': new_form,
    })


@clubs_admin_required
def manage_import(request):
    form = StudentImportForm()
    result = None
    if request.method == 'POST':
        if 'delete_all' in request.POST:
            if request.POST.get('confirm', '').strip().upper() == 'LÖSCHEN':
                count, _ = Student.objects.all().delete()
                messages.success(request, 'Alle Schüler:innen, Wahlcodes und Wahlen wurden gelöscht.')
            else:
                messages.error(request, 'Zum Löschen bitte LÖSCHEN in das Feld eingeben.')
            return redirect('clubs:import')

        form = StudentImportForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data.get('csv_file')
            text = decode_upload(upload.read()) if upload else form.cleaned_data['pasted']
            result = import_students(text)
            if result.created:
                messages.success(request, f'{len(result.created)} Schüler:innen importiert.')
            form = StudentImportForm()

    created_groups = sorted_groups(s.group for s in result.created) if result else []
    return render(request, 'clubs/manage_import.html', {
        'nav': 'import',
        'form': form,
        'result': result,
        'created_groups': created_groups,
        'total_count': Student.objects.count(),
    })


# ---------------------------------------------------------------------------
# Print views
# ---------------------------------------------------------------------------

def _qr_svg(data):
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    return mark_safe(img.to_string(encoding='unicode'))


def _print_context(request, **extra):
    context = {
        'setting': ClubSetting.get(),
        'groups': sorted_groups(Student.objects.values_list('group', flat=True)),
        'current_group': request.GET.get('klasse', ''),
    }
    context.update(extra)
    return context


@clubs_admin_required
def print_codes(request):
    group = request.GET.get('klasse', '')
    with_qr = request.GET.get('qr', '1') != '0'
    students = Student.objects.all()
    if group:
        students = students.filter(group=group)
    students = sorted(students, key=student_sort_key)
    base_url = request.build_absolute_uri(reverse('clubs:index'))
    for s in students:
        s.url = f'{base_url}?code={s.display_token}'
        s.qr = _qr_svg(s.url) if with_qr else ''

    sections = OrderedDict()
    for s in students:
        sections.setdefault(s.group, []).append(s)

    return render(request, 'clubs/print_codes.html', _print_context(
        request, sections=sections, base_url=base_url, with_qr=with_qr, print_view='codes',
    ))


@clubs_admin_required
def print_by_club(request):
    club_filter = request.GET.get('ag', '')
    clubs = _clubs_with_counts()
    if club_filter.isdigit():
        clubs = [c for c in clubs if c.pk == int(club_filter)]
    members = {}
    for s in _decorate(list(_student_queryset().filter(assigned__isnull=False))):
        members.setdefault(s.assigned_id, []).append(s)
    for club in clubs:
        club.members = sorted(members.get(club.pk, []), key=student_sort_key)

    return render(request, 'clubs/print_by_club.html', _print_context(
        request, clubs=clubs, all_clubs=Club.objects.all(), current_club=club_filter, print_view='by_club',
    ))


@clubs_admin_required
def print_by_group(request):
    group = request.GET.get('klasse', '')
    students = _student_queryset()
    if group:
        students = students.filter(group=group)
    sections = OrderedDict()
    for s in _decorate(sorted(students, key=student_sort_key)):
        sections.setdefault(s.group, []).append(s)

    return render(request, 'clubs/print_by_group.html', _print_context(
        request, sections=sections, print_view='by_group',
    ))
