"""Import, sorting and assignment helpers for the club election."""
import csv
import random
import re
from dataclasses import dataclass, field
from io import StringIO

from django.db import transaction

from .models import Club, Student

LAST_NAME_HEADERS = {'nachname', 'name', 'familienname', 'last_name', 'lastname', 'last', 'surname'}
FIRST_NAME_HEADERS = {'vorname', 'rufname', 'first_name', 'firstname', 'first'}
GROUP_HEADERS = {'klasse', 'lerngruppe', 'kurs', 'class', 'group', 'stufe'}


def group_sort_key(group):
    """Natural sort for class names: 5a < 6b < 10a < EF < Q1."""
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r'(\d+)', group or '')]


def student_sort_key(student):
    return (group_sort_key(student.group), student.last_name.casefold(), student.first_name.casefold())


def sorted_groups(groups):
    return sorted(set(groups), key=group_sort_key)


def decode_upload(raw_bytes):
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode('latin-1')


def _normalize_header(value):
    return re.sub(r'[\s\-.]', '_', (value or '').strip().casefold()).strip('_')


@dataclass
class ImportResult:
    created: list = field(default_factory=list)
    existing: int = 0
    errors: list = field(default_factory=list)


def parse_student_rows(text):
    """Return a list of (line_no, last_name, first_name, group) and a list of errors.

    Accepts ';', ',' or tab separated data with or without a header row.
    Without a header the column order Nachname, Vorname, Klasse is assumed.
    """
    text = text.strip('﻿')
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return [], ['Die Datei enthält keine Daten.']

    sample = '\n'.join(lines[:10])
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=';,\t').delimiter
    except csv.Error:
        delimiter = ';' if ';' in sample else ('\t' if '\t' in sample else ',')

    reader = list(csv.reader(StringIO('\n'.join(lines)), delimiter=delimiter))
    header = [_normalize_header(h) for h in reader[0]]

    def find(candidates):
        for i, h in enumerate(header):
            if h in candidates:
                return i
        return None

    idx_last = find(LAST_NAME_HEADERS)
    idx_first = find(FIRST_NAME_HEADERS)
    idx_group = find(GROUP_HEADERS)

    if idx_last is not None and idx_first is not None:
        data_rows = reader[1:]
        first_line = 2
    else:
        idx_last, idx_first, idx_group = 0, 1, 2
        data_rows = reader
        first_line = 1

    rows, errors = [], []
    for offset, row in enumerate(data_rows):
        line_no = first_line + offset

        def cell(i):
            if i is None or i >= len(row):
                return ''
            return row[i].strip()

        last, first, group = cell(idx_last), cell(idx_first), cell(idx_group)
        if not last or not first:
            errors.append(f'Zeile {line_no}: Vor- oder Nachname fehlt – übersprungen.')
            continue
        rows.append((line_no, last, first, group[:20]))
    return rows, errors


def _identity(last, first, group):
    return (last.casefold(), first.casefold(), group.casefold())


@transaction.atomic
def import_students(text):
    """Create students that are not in the database yet. Existing students keep their Wahlcode."""
    rows, errors = parse_student_rows(text)
    result = ImportResult(errors=errors)
    known = {_identity(s.last_name, s.first_name, s.group) for s in Student.objects.all()}
    for _line_no, last, first, group in rows:
        key = _identity(last, first, group)
        if key in known:
            result.existing += 1
            continue
        known.add(key)
        result.created.append(Student.objects.create(last_name=last, first_name=first, group=group))
    return result


@dataclass
class AssignmentResult:
    assigned: int = 0
    unplaced: list = field(default_factory=list)


@transaction.atomic
def auto_assign(reset=False, seed=None):
    """Assign students to clubs based on their wishes, respecting max_size.

    Round based: first everyone is tried with the 1st wish, then the remaining with
    the 2nd wish, then the 3rd. The order within a round is random, so nobody is
    preferred by alphabet or class. Existing (manual) assignments are kept unless
    reset=True.
    """
    rng = random.Random(seed)
    if reset:
        Student.objects.filter(choice__isnull=False).update(assigned=None)

    clubs = {c.id: c for c in Club.objects.all()}
    load = {cid: 0 for cid in clubs}
    for cid in Student.objects.filter(assigned__isnull=False).values_list('assigned_id', flat=True):
        if cid in load:
            load[cid] += 1

    remaining = list(
        Student.objects.filter(assigned__isnull=True, choice__isnull=False).select_related('choice')
    )
    rng.shuffle(remaining)

    result = AssignmentResult()
    changed = []
    for rank in (1, 2, 3):
        still_open = []
        for student in remaining:
            cid = getattr(student.choice, f'choice{rank}_id')
            club = clubs.get(cid)
            if club is not None and (club.max_size is None or load[cid] < club.max_size):
                student.assigned_id = cid
                load[cid] += 1
                changed.append(student)
            else:
                still_open.append(student)
        remaining = still_open

    Student.objects.bulk_update(changed, ['assigned'])
    result.assigned = len(changed)
    result.unplaced = sorted(remaining, key=student_sort_key)
    return result
