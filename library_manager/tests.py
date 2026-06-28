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
