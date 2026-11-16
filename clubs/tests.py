from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Club, ClubChoice, ClubSetting, Student
from .services import auto_assign, group_sort_key, parse_student_rows
from .tokens import ALPHABET, TOKEN_LENGTH, format_token, normalize_token


class TokenTests(TestCase):
    def test_student_gets_unique_token(self):
        a = Student.objects.create(last_name='A', first_name='A', group='5a')
        b = Student.objects.create(last_name='B', first_name='B', group='5a')
        self.assertEqual(len(a.token), TOKEN_LENGTH)
        self.assertTrue(set(a.token) <= set(ALPHABET))
        self.assertNotEqual(a.token, b.token)

    def test_normalize_and_format(self):
        self.assertEqual(normalize_token(' ab cd-efgh '), 'ABCDEFGH')
        self.assertEqual(format_token('ABCDEFGH'), 'ABCD-EFGH')


class ParsingTests(TestCase):
    def test_semicolon_with_header_and_extra_columns(self):
        rows, errors = parse_student_rows('ID;Klasse;Vorname;Nachname\n1;7a;Max;Müller\n2;7b;;Leer\n')
        self.assertEqual([r[1:] for r in rows], [('Müller', 'Max', '7a')])
        self.assertEqual(len(errors), 1)

    def test_tab_without_header(self):
        rows, errors = parse_student_rows('Muster\tErika\t10c\nMuster\tMax\t5a')
        self.assertEqual([r[1:] for r in rows], [('Muster', 'Erika', '10c'), ('Muster', 'Max', '5a')])
        self.assertEqual(errors, [])

    def test_group_sort_is_natural(self):
        groups = ['10a', 'Q1', '5b', 'EF', '5a', '9c']
        self.assertEqual(sorted(groups, key=group_sort_key), ['5a', '5b', '9c', '10a', 'EF', 'Q1'])


class AutoAssignTests(TestCase):
    def _student(self, name, *wishes):
        s = Student.objects.create(last_name=name, first_name='X', group='7a')
        ClubChoice.objects.create(student=s, **{f'choice{i + 1}': c for i, c in enumerate(wishes)})
        return s

    def test_respects_capacity_and_falls_back_to_next_wish(self):
        small = Club.objects.create(name='Klein', max_size=1)
        big = Club.objects.create(name='Groß', max_size=10)
        a = self._student('A', small, big)
        b = self._student('B', small, big)
        result = auto_assign(seed=1)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual(result.assigned, 2)
        self.assertEqual(sorted([a.assigned, b.assigned], key=lambda c: c.name), [big, small])

    def test_first_wishes_before_second_wishes(self):
        x = Club.objects.create(name='X', max_size=1)
        y = Club.objects.create(name='Y', max_size=1)
        # A wants X then Y, B wants Y first: B must get Y regardless of order
        for seed in range(10):
            Student.objects.all().delete()
            a = self._student('A', x, y)
            b = self._student('B', y, x)
            auto_assign(seed=seed)
            a.refresh_from_db()
            b.refresh_from_db()
            self.assertEqual((a.assigned, b.assigned), (x, y))

    def test_keeps_manual_assignments_and_reports_unplaced(self):
        x = Club.objects.create(name='X', max_size=1)
        manual = self._student('Manual', x)
        manual.assigned = x
        manual.save()
        other = self._student('Other', x)
        result = auto_assign()
        manual.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(manual.assigned, x)
        self.assertIsNone(other.assigned)
        self.assertEqual(result.unplaced, [other])


class StudentFlowTests(TestCase):
    def setUp(self):
        ClubSetting.objects.create(title='AG-Wahl', voting_open=True)
        self.clubs = [Club.objects.create(name=n, order=i) for i, n in enumerate(['Chor', 'Robotik', 'Schach'])]
        self.student = Student.objects.create(last_name='Muster', first_name='Max', group='7a')

    def _login(self, code=None):
        return self.client.post(reverse('clubs:index'), {'code': code or self.student.display_token.lower()})

    def test_wrong_code_is_rejected(self):
        response = self._login('AAAA-AAAA')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'nicht bekannt')

    def test_choice_requires_login(self):
        response = self.client.get(reverse('clubs:choose'))
        self.assertRedirects(response, reverse('clubs:index'))

    def test_vote_and_change(self):
        self.assertRedirects(self._login(), reverse('clubs:choose'))
        c1, c2, c3 = self.clubs
        self.client.post(reverse('clubs:choose'), {'choice1': c1.pk, 'choice2': c2.pk, 'choice3': c3.pk})
        self.client.post(reverse('clubs:choose'), {'choice1': c3.pk, 'choice2': c2.pk, 'choice3': c1.pk})
        self.assertEqual(ClubChoice.objects.count(), 1)
        self.assertEqual(self.student.choice.choice1, c3)

    def test_duplicate_wishes_rejected(self):
        self._login()
        c1, c2, _ = self.clubs
        response = self.client.post(reverse('clubs:choose'), {'choice1': c1.pk, 'choice2': c1.pk, 'choice3': c2.pk})
        self.assertContains(response, 'verschiedene')
        self.assertFalse(ClubChoice.objects.exists())

    def test_closed_voting_rejects_changes(self):
        ClubSetting.objects.update(voting_open=False)
        self._login()
        c1, c2, c3 = self.clubs
        self.client.post(reverse('clubs:choose'), {'choice1': c1.pk, 'choice2': c2.pk, 'choice3': c3.pk})
        self.assertFalse(ClubChoice.objects.exists())


class ManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user('lehrer', password='x')
        self.admin.groups.add(Group.objects.create(name='clubs_admin'))
        self.client.force_login(self.admin)

    def test_non_admin_has_no_access(self):
        self.client.force_login(get_user_model().objects.create_user('other', password='x'))
        response = self.client.get(reverse('clubs:manage'))
        self.assertEqual(response.status_code, 302)

    def test_import_keeps_existing_codes(self):
        existing = Student.objects.create(last_name='Muster', first_name='Max', group='7a')
        token = existing.token
        upload = SimpleUploadedFile(
            'sus.csv', 'Nachname;Vorname;Klasse\nmuster;max;7A\nMüller;Lea;7b\n'.encode('cp1252'),
            content_type='text/csv',
        )
        response = self.client.post(reverse('clubs:import'), {'csv_file': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 2)
        existing.refresh_from_db()
        self.assertEqual(existing.token, token)
        self.assertTrue(Student.objects.filter(last_name='Müller', group='7b').exists())

    def test_manual_assignment(self):
        club = Club.objects.create(name='Chor')
        student = Student.objects.create(last_name='A', first_name='B', group='5a')
        response = self.client.post(
            reverse('clubs:manage_students') + '?klasse=5a',
            {'save_assignments': '1', f'assign-{student.pk}': str(club.pk)},
        )
        self.assertRedirects(response, reverse('clubs:manage_students') + '?klasse=5a')
        student.refresh_from_db()
        self.assertEqual(student.assigned, club)

    def test_manage_clubs_crud(self):
        response = self.client.post(reverse('clubs:manage_clubs'), {
            'add_club': '1', 'new-name': 'Theater', 'new-max_size': '12', 'new-order': '1',
        })
        self.assertRedirects(response, reverse('clubs:manage_clubs'))
        club = Club.objects.get(name='Theater')
        self.client.post(reverse('clubs:manage_clubs'), {
            'save_club': '1', 'club_id': club.pk,
            f'club{club.pk}-name': 'Theater-AG', f'club{club.pk}-max_size': '15', f'club{club.pk}-order': '2',
        })
        club.refresh_from_db()
        self.assertEqual((club.name, club.max_size), ('Theater-AG', 15))

    def test_overview_and_print_views_render(self):
        club = Club.objects.create(name='Chor', max_size=1)
        for name in ('A', 'B'):
            s = Student.objects.create(last_name=name, first_name='X', group='5a', assigned=club)
            ClubChoice.objects.create(student=s, choice1=club)
        response = self.client.get(reverse('clubs:manage'))
        self.assertContains(response, 'Überbelegt')
        for name in ('print_codes', 'print_by_club', 'print_by_group'):
            response = self.client.get(reverse(f'clubs:{name}'))
            self.assertEqual(response.status_code, 200, name)
        response = self.client.get(reverse('clubs:print_codes') + '?klasse=5a')
        self.assertContains(response, '<svg')
        self.assertContains(response, Student.objects.first().display_token)
