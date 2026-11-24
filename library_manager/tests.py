from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    InventoryItem,
    LibraryBorrowedItem,
    LibraryCategoryShelfmark,
    LibraryLocation,
    LibraryStatus,
)


class LibraryBorrowExtensionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='admin',
            password='secret',
            is_staff=True,
        )
        self.category = LibraryCategoryShelfmark.objects.create(category='Test', shelfmark='T1')
        self.location = LibraryLocation.objects.create(name='Aula')
        self.status = LibraryStatus.objects.create(name='verfügbar')
        self.book = InventoryItem.objects.create(
            author='Autor',
            title='Titel',
            category_shelfmark=self.category,
            inventory_number=1,
            location=self.location,
            status=self.status,
        )
        self.borrowed_item = LibraryBorrowedItem.objects.create(
            first_name='Max',
            surname='Mustermann',
            school_class='5a',
            book=self.book,
            borrowing_date=timezone.now().date(),
            return_date=date(2026, 1, 1),
        )

    def test_extend_book_increases_return_date(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('extend_book', args=[self.borrowed_item.id]),
            {'days': '7'},
            follow=True,
        )

        self.borrowed_item.refresh_from_db()

        self.assertRedirects(response, reverse('returnlist'))
        self.assertEqual(self.borrowed_item.return_date, date(2026, 1, 8))

    def test_extend_book_with_specific_return_date(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('extend_book', args=[self.borrowed_item.id]),
            {'return_date': '2026-01-15'},
            follow=True,
        )

        self.borrowed_item.refresh_from_db()

        self.assertRedirects(response, reverse('returnlist'))
        self.assertEqual(self.borrowed_item.return_date, date(2026, 1, 15))


class LibraryEditRedirectTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='secret', is_staff=True)
        self.client.force_login(self.user)
        self.category = LibraryCategoryShelfmark.objects.create(category='Test', shelfmark='T1')
        self.location = LibraryLocation.objects.create(name='Aula')
        self.status = LibraryStatus.objects.create(name='verfügbar')
        self.book = InventoryItem.objects.create(
            author='Autor', title='Titel', category_shelfmark=self.category,
            inventory_number=1, location=self.location, status=self.status,
        )
        self.form_data = {
            'author': 'Autor', 'title': 'Titel', 'location': self.location.id,
            'category_shelfmark': self.category.id, 'inventory_number': 1, 'notes': '',
        }

    def test_redirect_preserves_filters(self):
        url = reverse('edit', args=[self.book.id]) + (
            f'?filter_category={self.category.id}&filter_status={self.status.id}&filter_text=Gr%C3%BCn+%26+Co'
        )
        response = self.client.post(url, self.form_data)
        self.assertRedirects(
            response,
            reverse('inventory') + f'?filter_category={self.category.id}&filter_status={self.status.id}'
            f'&filter_text=Gr%C3%BCn+%26+Co&location={self.location.id}',
        )

    def test_redirect_cannot_leave_site(self):
        url = reverse('edit', args=[self.book.id]) + (
            '?filter_category=//evil.example&filter_status=x&filter_text=//evil.example/&next=//evil.example'
        )
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, 302)
        location = response['Location']
        self.assertTrue(location.startswith(reverse('inventory') + '?'))
        self.assertIn('filter_category=0&filter_status=0', location)
