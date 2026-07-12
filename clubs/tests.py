from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Club, ClubChoice


class ClubManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_manage_view_can_create_update_and_delete_clubs(self):
        club_a = Club.objects.create(name='Alpha', order=2)
        club_b = Club.objects.create(name='Beta', order=1)

        response = self.client.post(reverse('clubs:manage'), {
            'clubs_form': '1',
            f'club-name-{club_a.id}': 'Alpha neu',
            f'club-order-{club_a.id}': '5',
            f'club-max_size-{club_a.id}': '12',
            f'club-delete-{club_b.id}': '1',
            'new-club-name': 'Gamma',
            'new-club-order': '3',
            'new-club-max_size': '8',
        })

        self.assertEqual(response.status_code, 302)
        club_a.refresh_from_db()
        self.assertEqual(club_a.name, 'Alpha neu')
        self.assertEqual(club_a.order, 5)
        self.assertEqual(club_a.max_size, 12)
        self.assertFalse(Club.objects.filter(pk=club_b.pk).exists())
        self.assertTrue(Club.objects.filter(name='Gamma').exists())

    def test_csv_import_creates_choice_rows_and_matches_existing_names(self):
        club = Club.objects.create(name='AG 1', order=1)
        csv_file = SimpleUploadedFile(
            'students.csv',
            b'first_name,last_name\nMax,Mustermann\n',
            content_type='text/csv',
        )

        response = self.client.post(
            reverse('clubs:manage'),
            data={'import_csv': '1', 'csv_file': csv_file},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        choice = ClubChoice.objects.get(first_name='Max', last_name='Mustermann')
        self.assertIsNone(choice.choice1)
        self.assertIsNone(choice.choice2)
        self.assertIsNone(choice.choice3)

        choose_response = self.client.post(reverse('clubs:choose'), {
            'first_name': 'Max',
            'last_name': 'Mustermann',
            'choice1': str(club.id),
            'choice2': '',
            'choice3': '',
        })

        self.assertEqual(choose_response.status_code, 302)
        choice.refresh_from_db()
        self.assertEqual(choice.choice1, club)
        self.assertEqual(ClubChoice.objects.filter(first_name='Max', last_name='Mustermann').count(), 1)
