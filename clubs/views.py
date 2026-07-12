from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from .forms import ClubChoiceForm
from .models import Club, ClubChoice
import csv
from io import StringIO, TextIOWrapper
from django.db import transaction


def _parse_optional_int(value, default=None):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_teacher(user):
    return user.is_staff or user.groups.filter(name='teachers').exists()


def index(request):
    clubs = Club.objects.all()
    return render(request, 'clubs/index.html', {'clubs': clubs})


@login_required
def choose_club(request):
    if request.method == 'POST':
        form = ClubChoiceForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name'].strip()
            last_name = form.cleaned_data['last_name'].strip()
            choice = ClubChoice.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
            if choice is None:
                choice = form.save(commit=False)
            else:
                choice.choice1 = form.cleaned_data.get('choice1')
                choice.choice2 = form.cleaned_data.get('choice2')
                choice.choice3 = form.cleaned_data.get('choice3')

            choice.first_name = first_name
            choice.last_name = last_name
            choice.save()
            choice.apply_first_choice_if_available()
            messages.success(request, 'Deine Angaben wurden gespeichert.')
            return redirect('clubs:index')
    else:
        form = ClubChoiceForm()
    return render(request, 'clubs/choose.html', {'form': form})


@user_passes_test(is_teacher)
def manage_assignments(request):
    """Protected management view: list students, show assigned and allow quick edit via dropdowns."""
    clubs = Club.objects.all().order_by('order', 'name')
    students = ClubChoice.objects.all().select_related('assigned', 'choice1', 'choice2', 'choice3')
    if request.method == 'POST':
        if request.POST.get('import_csv') and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            with transaction.atomic():
                content = csv_file.read().decode('utf-8-sig')
                reader = csv.DictReader(StringIO(content))
                created = 0
                for row in reader:
                    first = (row.get('first_name') or row.get('vorname') or row.get('first') or '').strip()
                    last = (row.get('last_name') or row.get('nachname') or row.get('last') or '').strip()
                    if first and last:
                        exists = ClubChoice.objects.filter(first_name__iexact=first, last_name__iexact=last).exists()
                        if not exists:
                            ClubChoice.objects.create(first_name=first, last_name=last)
                            created += 1
                messages.success(request, f'Datei importiert und {created} neue Einträge als Platzhalter angelegt.')
            return redirect('clubs:manage')

        club_updates = 0
        club_creations = 0
        club_deletions = 0

        for key, val in request.POST.items():
            if key.startswith('club-name-'):
                try:
                    cid = int(key.split('-', 2)[2])
                    club = Club.objects.get(pk=cid)
                    name = (val or '').strip()
                    if name:
                        club.name = name
                        club.save(update_fields=['name'])
                        club_updates += 1
                except (ValueError, Club.DoesNotExist):
                    continue

            elif key.startswith('club-order-'):
                try:
                    cid = int(key.split('-', 2)[2])
                    club = Club.objects.get(pk=cid)
                    order = _parse_optional_int(val, default=club.order)
                    if order is not None:
                        club.order = order
                        club.save(update_fields=['order'])
                        club_updates += 1
                except (ValueError, Club.DoesNotExist):
                    continue

            elif key.startswith('club-max_size-'):
                try:
                    cid = int(key.split('-', 2)[2])
                    club = Club.objects.get(pk=cid)
                    max_size = _parse_optional_int(val, default=None)
                    club.max_size = max_size
                    club.save(update_fields=['max_size'])
                    club_updates += 1
                except (ValueError, Club.DoesNotExist):
                    continue

            elif key.startswith('club-delete-'):
                try:
                    cid = int(key.split('-', 2)[2])
                    Club.objects.filter(pk=cid).delete()
                    club_deletions += 1
                except ValueError:
                    continue

        new_name = (request.POST.get('new-club-name') or '').strip()
        if new_name:
            new_order = _parse_optional_int(request.POST.get('new-club-order'), default=0)
            new_max_size = _parse_optional_int(request.POST.get('new-club-max_size'), default=None)
            Club.objects.create(name=new_name, order=new_order or 0, max_size=new_max_size)
            club_creations += 1

        for key, val in request.POST.items():
            if key.startswith('assign-'):
                try:
                    cid = int(key.split('-', 1)[1])
                    sc = ClubChoice.objects.get(pk=cid)
                    if val == '':
                        sc.assigned = None
                    else:
                        try:
                            club = Club.objects.get(pk=int(val))
                            sc.assigned = club
                        except Club.DoesNotExist:
                            sc.assigned = None
                    sc.save()
                except Exception:
                    continue

        message_parts = []
        if club_updates:
            message_parts.append(f'{club_updates} AG geändert')
        if club_creations:
            message_parts.append(f'{club_creations} AG angelegt')
        if club_deletions:
            message_parts.append(f'{club_deletions} AG gelöscht')
        message_parts.append('Zuordnungen aktualisiert.')
        messages.success(request, ' '.join(message_parts))
        return redirect('clubs:manage')

    # compute counts per club
    counts = {club.id: club.assigned_students.count() for club in clubs}
    return render(request, 'clubs/manage.html', {'students': students, 'clubs': clubs, 'counts': counts})
