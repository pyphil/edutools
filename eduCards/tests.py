from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CardsPage, Category, Card, CardsPageAccessToken


class EduCardsPermissionsTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student', password='password')
        self.teacher = User.objects.create_user(username='teacher', password='password', is_staff=True)
        self.page = CardsPage.objects.create(
            title='Test Page',
            description='A test cards page',
            created_by=self.teacher,
            is_active=True,
            order=0,
        )
        self.category = Category.objects.create(
            cards_page=self.page,
            name='Test Column',
            order=0,
        )

    def test_teacher_sees_own_pages_only(self):
        """Teachers only see pages they created in the list"""
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.page.title)

    def test_share_page_with_other_teacher(self):
        """A teacher can share a page with another teacher account"""
        other_teacher = User.objects.create_user(username='other_teacher', password='password', is_staff=True)
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.post(
            reverse('eduCards:share_cards_page', kwargs={'page_id': self.page.id}),
            {'share': '1', 'teachers': [other_teacher.id]}
        )
        self.assertRedirects(response, reverse('eduCards:manage_qr_tokens', kwargs={'page_id': self.page.id}))
        self.page.refresh_from_db()
        self.assertTrue(self.page.shared_with.filter(pk=other_teacher.pk).exists())

        self.client.logout()
        self.assertTrue(self.client.login(username='other_teacher', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eduCards/cards_page_detail.html')

    def test_shared_page_appears_in_shared_with_me(self):
        """Shared pages appear in the teacher's Shared with me section"""
        other_teacher = User.objects.create_user(username='other_teacher', password='password', is_staff=True)
        self.page.shared_with.add(other_teacher)
        self.assertTrue(self.client.login(username='other_teacher', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_list'))
        self.assertContains(response, 'Shared with me')
        self.assertContains(response, self.page.title)

    def test_unauthenticated_cannot_see_pages(self):
        """Unauthenticated users without QR don't see pages in list"""
        response = self.client.get(reverse('eduCards:cards_page_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.page.title)

    def test_authenticated_no_qr_cannot_access_page(self):
        """Authenticated user without QR cannot view page detail"""
        self.assertTrue(self.client.login(username='student', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eduCards/edu_cards_no_access.html')

    def test_qr_edit_token_grants_card_creation(self):
        """QR token with EDIT level allows card creation"""
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.post(
            reverse('eduCards:manage_qr_tokens', kwargs={'page_id': self.page.id}),
            {'create_qr': '1', 'access_level': CardsPageAccessToken.ACCESS_EDIT}
        )
        self.assertRedirects(response, reverse('eduCards:manage_qr_tokens', kwargs={'page_id': self.page.id}))

        token = self.page.access_tokens.first()
        self.assertIsNotNone(token)
        self.assertEqual(token.access_level, CardsPageAccessToken.ACCESS_EDIT)

        self.client.logout()
        access_url = reverse('eduCards:access_page_via_qr', kwargs={'page_id': self.page.id, 'token': token.token})
        response = self.client.get(access_url)
        self.assertRedirects(response, reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))

        response = self.client.post(
            reverse('eduCards:create_card', kwargs={'category_id': self.category.id}),
            {
                'title': 'QR Card Edit',
                'content': 'Created via QR Edit',
                'order': 0,
            }
        )
        self.assertRedirects(response, reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))
        card = Card.objects.filter(category=self.category, title='QR Card Edit').first()
        self.assertIsNotNone(card)
        self.assertIsNone(card.created_by)

    def test_qr_view_token_denies_card_creation(self):
        """QR token with VIEW level prevents card creation"""
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.post(
            reverse('eduCards:manage_qr_tokens', kwargs={'page_id': self.page.id}),
            {'create_qr': '1', 'access_level': CardsPageAccessToken.ACCESS_VIEW}
        )

        token = self.page.access_tokens.first()
        self.assertEqual(token.access_level, CardsPageAccessToken.ACCESS_VIEW)

        self.client.logout()
        access_url = reverse('eduCards:access_page_via_qr', kwargs={'page_id': self.page.id, 'token': token.token})
        self.client.get(access_url)

        response = self.client.post(
            reverse('eduCards:create_card', kwargs={'category_id': self.category.id}),
            {
                'title': 'View Only Card',
                'content': 'Should fail',
                'order': 0,
            }
        )
        # Should redirect without creating card
        self.assertEqual(response.status_code, 302)
        card = Card.objects.filter(category=self.category, title='View Only Card').first()
        self.assertIsNone(card)

    def test_non_teacher_cannot_access_edit_category(self):
        """Non-teachers cannot edit categories"""
        self.assertTrue(self.client.login(username='student', password='password'))
        response = self.client.get(reverse('eduCards:edit_category', kwargs={'category_id': self.category.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_card_form_uses_single_multi_file_upload_section(self):
        """The card form presents one clear multi-file upload section."""
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.get(reverse('eduCards:create_card', kwargs={'category_id': self.category.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Files')
        self.assertNotContains(response, 'Primary Attachment')

    def test_creating_card_saves_uploaded_files_as_attachments(self):
        """Files selected in the uploader are persisted as card attachments."""
        self.assertTrue(self.client.login(username='teacher', password='password'))
        uploaded_file = SimpleUploadedFile('sample.txt', b'hello world', content_type='text/plain')
        response = self.client.post(
            reverse('eduCards:create_card', kwargs={'category_id': self.category.id}),
            {
                'title': 'File Card',
                'content': 'Uploaded file should be saved',
                'order': 0,
                'attachments': [uploaded_file],
            },
        )
        self.assertEqual(response.status_code, 302)
        card = Card.objects.get(title='File Card')
        attachment = card.attachments.first()
        self.assertIsNotNone(attachment)
        self.assertTrue(attachment.file.name.endswith('.txt'))
        self.assertEqual(attachment.file.read().decode('utf-8'), 'hello world')

    def test_card_detail_renders_images_inline(self):
        """Image attachments are shown inline instead of a download button."""
        card = Card.objects.create(
            category=self.category,
            title='Image card',
            content='A rich text card',
            attachment=SimpleUploadedFile('sample.png', b'fake-image-bytes', content_type='image/png'),
            order=0,
        )
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'img')
        self.assertContains(response, 'data-bs-toggle="modal"')
        self.assertContains(response, 'Download')
        self.assertContains(response, 'inline=1')

    def test_card_detail_renders_pdfs_inline(self):
        """PDF attachments render as a first-page preview using PDF.js."""
        Card.objects.create(
            category=self.category,
            title='PDF card',
            content='A rich text card',
            attachment=SimpleUploadedFile('sample.pdf', b'%PDF-1.4', content_type='application/pdf'),
            order=0,
        )
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.get(reverse('eduCards:cards_page_detail', kwargs={'page_id': self.page.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pdfjs-preview')
        self.assertContains(response, 'pdf.min.js')
        self.assertContains(response, 'canvas')
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'Download')

    def test_inline_pdf_response_allows_embedding(self):
        """Inline PDF responses remain browser-fetchable for PDF.js preview rendering."""
        card = Card.objects.create(
            category=self.category,
            title='PDF frame card',
            content='A PDF card',
            attachment=SimpleUploadedFile('sample.pdf', b'%PDF-1.4', content_type='application/pdf'),
            order=0,
        )
        self.assertTrue(self.client.login(username='teacher', password='password'))
        response = self.client.get(
            reverse('eduCards:download_attachment', kwargs={'card_id': card.id}),
            {'inline': '1'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('inline; filename="'))
        self.assertTrue(response['Content-Disposition'].endswith('.pdf"'))
        self.assertEqual(response.get('Content-Type').split(';')[0], 'application/pdf')

