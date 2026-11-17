import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CardsPage, Category, Card, CardAttachment, CardComment, CardReaction, CardsPageAccessToken
from .sanitize import sanitize_html
from .views import youtube_id

TEMP_MEDIA = tempfile.mkdtemp(prefix='educards-test-media-')


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EduCardsTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student', password='password')
        self.teacher = User.objects.create_user(username='teacher', password='password', is_staff=True)
        self.other_teacher = User.objects.create_user(username='other_teacher', password='password', is_staff=True)
        self.page = CardsPage.objects.create(
            title='Test Page',
            description='A test cards page',
            created_by=self.teacher,
            is_active=True,
            order=0,
        )
        self.category = Category.objects.create(cards_page=self.page, name='Test Column', order=0)

    # helpers
    def url(self, name, **kwargs):
        return reverse(f'eduCards:{name}', kwargs=kwargs)

    def board_url(self):
        return self.url('cards_page_detail', page_id=self.page.id)

    def login_teacher(self, username='teacher'):
        self.assertTrue(self.client.login(username=username, password='password'))

    def grant_qr(self, level=CardsPageAccessToken.ACCESS_EDIT, client=None):
        token = CardsPageAccessToken.objects.create(
            cards_page=self.page, token=f'tok-{level}-{CardsPageAccessToken.objects.count()}',
            access_level=level, created_by=self.teacher,
        )
        (client or self.client).get(self.url('access_page_via_qr', page_id=self.page.id, token=token.token))
        return token

    def make_card(self, **kwargs):
        data = {'category': self.category, 'title': 'Card', 'content': '<p>Text</p>', 'order': 0}
        data.update(kwargs)
        return Card.objects.create(**data)

    def post_json(self, url, payload):
        return self.client.post(url, data=json.dumps(payload), content_type='application/json')


class EduCardsPermissionsTests(EduCardsTestCase):
    def test_teacher_sees_own_pages_only(self):
        CardsPage.objects.create(title='Foreign Page', created_by=self.other_teacher)
        self.login_teacher()
        response = self.client.get(self.url('cards_page_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.page.title)
        self.assertNotContains(response, 'Foreign Page')

    def test_share_page_with_other_teacher(self):
        self.login_teacher()
        response = self.client.post(
            self.url('share_cards_page', page_id=self.page.id),
            {'share': '1', 'teachers': [self.other_teacher.id]}
        )
        self.assertRedirects(response, self.url('manage_qr_tokens', page_id=self.page.id))
        self.assertTrue(self.page.shared_with.filter(pk=self.other_teacher.pk).exists())

        self.client.logout()
        self.login_teacher('other_teacher')
        response = self.client.get(self.board_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eduCards/cards_page_detail.html')

    def test_shared_page_appears_in_shared_with_me(self):
        self.page.shared_with.add(self.other_teacher)
        self.login_teacher('other_teacher')
        response = self.client.get(self.url('cards_page_list'))
        self.assertContains(response, 'Mit mir geteilt')
        self.assertContains(response, self.page.title)

    def test_unauthenticated_cannot_see_pages(self):
        response = self.client.get(self.url('cards_page_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.page.title)

    def test_authenticated_no_qr_cannot_access_page(self):
        self.assertTrue(self.client.login(username='student', password='password'))
        response = self.client.get(self.board_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eduCards/edu_cards_no_access.html')

    def test_non_member_teacher_cannot_view_or_edit(self):
        card = self.make_card()
        self.login_teacher('other_teacher')
        self.assertTemplateUsed(self.client.get(self.board_url()), 'eduCards/edu_cards_no_access.html')
        for url in (
            self.url('edit_cards_page', page_id=self.page.id),
            self.url('share_cards_page', page_id=self.page.id),
            self.url('create_category', page_id=self.page.id),
            self.url('edit_category', category_id=self.category.id),
            self.url('delete_category', category_id=self.category.id),
            self.url('edit_card', card_id=card.id),
            self.url('delete_card', card_id=card.id),
        ):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.assertEqual(self.client.post(self.url('delete_card', card_id=card.id)).status_code, 403)
        self.assertTrue(Card.objects.filter(pk=card.pk).exists())

    def test_qr_edit_token_grants_card_creation(self):
        self.login_teacher()
        response = self.client.post(
            self.url('manage_qr_tokens', page_id=self.page.id),
            {'create_qr': '1', 'access_level': CardsPageAccessToken.ACCESS_EDIT}
        )
        self.assertRedirects(response, self.url('manage_qr_tokens', page_id=self.page.id))
        token = self.page.access_tokens.first()
        self.assertEqual(token.access_level, CardsPageAccessToken.ACCESS_EDIT)

        self.client.logout()
        response = self.client.get(self.url('access_page_via_qr', page_id=self.page.id, token=token.token))
        self.assertRedirects(response, self.board_url())

        response = self.client.post(
            self.url('create_card', category_id=self.category.id),
            {'title': 'QR Card Edit', 'content': 'Created via QR Edit', 'author_name': 'Mia'}
        )
        self.assertRedirects(response, self.board_url())
        card = Card.objects.get(category=self.category, title='QR Card Edit')
        self.assertIsNone(card.created_by)
        self.assertEqual(card.author_name, 'Mia')
        self.assertTrue(card.guest_key)
        self.assertTrue(card.is_approved)

    def test_qr_view_token_denies_card_creation(self):
        self.grant_qr(CardsPageAccessToken.ACCESS_VIEW)
        self.assertEqual(self.client.get(self.board_url()).status_code, 200)
        response = self.client.post(
            self.url('create_card', category_id=self.category.id),
            {'title': 'View Only Card', 'content': 'Should fail'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Card.objects.filter(title='View Only Card').exists())

    def test_non_teacher_cannot_access_edit_category(self):
        self.assertTrue(self.client.login(username='student', password='password'))
        response = self.client.get(self.url('edit_category', category_id=self.category.id))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_guest_can_edit_and_delete_only_own_cards(self):
        self.grant_qr()
        self.client.post(self.url('create_card', category_id=self.category.id), {'title': 'Mine', 'content': 'x'})
        mine = Card.objects.get(title='Mine')
        foreign = self.make_card(title='Teacher card', created_by=self.teacher)

        response = self.client.post(self.url('edit_card', card_id=mine.id), {'title': 'Mine edited', 'content': 'y'})
        self.assertEqual(response.status_code, 302)
        mine.refresh_from_db()
        self.assertEqual(mine.title, 'Mine edited')

        self.assertEqual(self.client.get(self.url('edit_card', card_id=foreign.id)).status_code, 403)
        self.assertEqual(self.client.post(self.url('delete_card', card_id=foreign.id)).status_code, 403)

        other_guest = self.client_class()
        self.grant_qr(client=other_guest)
        self.assertEqual(other_guest.post(self.url('delete_card', card_id=mine.id)).status_code, 403)

        self.client.post(self.url('delete_card', card_id=mine.id))
        self.assertFalse(Card.objects.filter(pk=mine.pk).exists())

    def test_anonymous_without_session_is_sent_to_login_for_edit(self):
        card = self.make_card()
        response = self.client.get(self.url('edit_card', card_id=card.id))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_only_creator_can_delete_board(self):
        self.page.shared_with.add(self.other_teacher)
        self.login_teacher('other_teacher')
        self.assertEqual(self.client.post(self.url('delete_cards_page', page_id=self.page.id)).status_code, 403)
        self.client.logout()
        self.login_teacher()
        self.assertContains(self.client.get(self.url('delete_cards_page', page_id=self.page.id)), 'Wirklich löschen?')
        response = self.client.post(self.url('delete_cards_page', page_id=self.page.id))
        self.assertRedirects(response, self.url('cards_page_list'))
        self.assertFalse(CardsPage.objects.filter(pk=self.page.pk).exists())


class EduCardsCardTests(EduCardsTestCase):
    def test_card_form_uses_single_multi_file_upload_section(self):
        self.login_teacher()
        response = self.client.get(self.url('create_card', category_id=self.category.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dateien')
        self.assertContains(response, 'name="attachments"', count=1)
        # teachers don't get the guest name field
        self.assertNotContains(response, 'name="author_name"')

    def test_creating_card_saves_uploaded_files_as_attachments(self):
        self.login_teacher()
        uploaded_file = SimpleUploadedFile('sample.txt', b'hello world', content_type='text/plain')
        response = self.client.post(
            self.url('create_card', category_id=self.category.id),
            {'title': 'File Card', 'content': '', 'attachments': [uploaded_file]},
        )
        self.assertEqual(response.status_code, 302)
        card = Card.objects.get(title='File Card')
        attachment = card.attachments.first()
        self.assertTrue(attachment.file.name.endswith('.txt'))
        self.assertEqual(attachment.file.read().decode('utf-8'), 'hello world')
        self.assertEqual(card.created_by, self.teacher)

    def test_disallowed_upload_type_is_rejected(self):
        self.login_teacher()
        response = self.client.post(
            self.url('create_card', category_id=self.category.id),
            {'title': 'Evil', 'content': 'x', 'attachments': [SimpleUploadedFile('evil.html', b'<script>', content_type='text/html')]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'nicht erlaubt')
        self.assertFalse(Card.objects.filter(title='Evil').exists())

    def test_empty_card_is_rejected(self):
        self.login_teacher()
        response = self.client.post(self.url('create_card', category_id=self.category.id), {'title': 'Empty', 'content': '<p>&nbsp;</p>'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Card.objects.filter(title='Empty').exists())

    def test_new_cards_are_appended_and_can_change_column(self):
        self.login_teacher()
        other = Category.objects.create(cards_page=self.page, name='Other', order=1)
        self.make_card(title='First', order=5)
        self.client.post(self.url('create_card', category_id=self.category.id), {'title': 'Second', 'content': 'x'})
        self.assertEqual(Card.objects.get(title='Second').order, 6)
        card = Card.objects.get(title='Second')
        self.client.post(self.url('edit_card', card_id=card.id), {'title': 'Second', 'content': 'x', 'category': other.id, 'color': 'yellow'})
        card.refresh_from_db()
        self.assertEqual(card.category, other)
        self.assertEqual(card.color, 'yellow')
        self.assertEqual(card.last_modified_by, self.teacher)

    def test_card_content_is_sanitized(self):
        self.grant_qr()
        self.client.post(self.url('create_card', category_id=self.category.id), {
            'title': 'XSS',
            'content': '<p onclick="alert(1)">Hi<script>alert(2)</script> <a href="javascript:alert(3)">x</a></p>',
        })
        card = Card.objects.get(title='XSS')
        self.assertNotIn('script', card.content)
        self.assertNotIn('onclick', card.content)
        self.assertNotIn('javascript', card.content)
        self.assertIn('Hi', card.content)

    def test_legacy_unsafe_content_is_sanitized_on_render(self):
        self.make_card(title='Legacy', content='<img src=x onerror=alert(1)><b>bold</b>')
        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertNotContains(response, 'onerror')
        self.assertContains(response, '<b>bold</b>', html=False)

    def test_card_detail_renders_images_inline(self):
        self.make_card(
            title='Image card',
            attachment=SimpleUploadedFile('sample.png', b'fake-image-bytes', content_type='image/png'),
        )
        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img')
        self.assertContains(response, 'data-bs-toggle="modal"')
        self.assertContains(response, 'Download')
        self.assertContains(response, 'inline=1')

    def test_card_detail_renders_pdfs_inline(self):
        card = self.make_card(title='PDF card')
        CardAttachment.objects.create(card=card, file=SimpleUploadedFile('sample.pdf', b'%PDF-1.4'))
        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertContains(response, 'pdfjs-preview')
        self.assertContains(response, 'pdf.min.js')
        self.assertContains(response, 'canvas')
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'Download')

    def test_inline_pdf_response_allows_embedding(self):
        card = self.make_card(
            title='PDF frame card',
            attachment=SimpleUploadedFile('sample.pdf', b'%PDF-1.4', content_type='application/pdf'),
        )
        self.login_teacher()
        response = self.client.get(self.url('download_attachment', card_id=card.id), {'inline': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('inline; filename="'))
        self.assertTrue(response['Content-Disposition'].endswith('.pdf"'))
        self.assertEqual(response.get('Content-Type').split(';')[0], 'application/pdf')

    def test_non_previewable_files_are_never_served_inline(self):
        card = self.make_card()
        attachment = CardAttachment.objects.create(card=card, file=SimpleUploadedFile('page.txt', b'hi'))
        self.login_teacher()
        response = self.client.get(self.url('download_attachment', card_id=card.id),
                                   {'inline': '1', 'attachment_id': attachment.id})
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))

    def test_youtube_link_is_embedded_after_consent(self):
        self.make_card(title='Video', content='', link_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.make_card(title='Link', content='', link_url='https://www.example.org/page')
        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertContains(response, 'data-youtube-id="dQw4w9WgXcQ"')
        self.assertNotContains(response, '<iframe')
        self.assertContains(response, 'example.org')

    def test_youtube_id_parsing(self):
        self.assertEqual(youtube_id('https://youtu.be/dQw4w9WgXcQ?t=3'), 'dQw4w9WgXcQ')
        self.assertEqual(youtube_id('https://m.youtube.com/watch?v=dQw4w9WgXcQ&list=x'), 'dQw4w9WgXcQ')
        self.assertEqual(youtube_id('https://www.youtube.com/shorts/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertIsNone(youtube_id('https://evil.example/watch?v=dQw4w9WgXcQ'))
        self.assertIsNone(youtube_id('https://youtube.com/watch?v=<script>'))
        self.assertIsNone(youtube_id(''))


class EduCardsModerationTests(EduCardsTestCase):
    def setUp(self):
        super().setUp()
        self.page.require_approval = True
        self.page.save()

    def test_guest_cards_need_approval(self):
        self.grant_qr()
        self.client.post(self.url('create_card', category_id=self.category.id), {'title': 'Pending idea', 'content': 'x'})
        card = Card.objects.get(title='Pending idea')
        self.assertFalse(card.is_approved)
        # the author sees the card with a hint
        response = self.client.get(self.board_url())
        self.assertContains(response, 'Pending idea')
        self.assertContains(response, 'Wartet auf Freigabe')

        other_guest = self.client_class()
        self.grant_qr(client=other_guest)
        self.assertNotContains(other_guest.get(self.board_url()), 'Pending idea')

        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertContains(response, 'Pending idea')
        self.assertContains(response, 'wartet auf Freigabe')
        self.client.post(self.url('approve_card', card_id=card.id))
        card.refresh_from_db()
        self.assertTrue(card.is_approved)
        self.assertContains(other_guest.get(self.board_url()), 'Pending idea')

    def test_teacher_cards_are_published_immediately(self):
        self.login_teacher()
        self.client.post(self.url('create_card', category_id=self.category.id), {'title': 'Teacher idea', 'content': 'x'})
        self.assertTrue(Card.objects.get(title='Teacher idea').is_approved)

    def test_guest_cannot_approve_or_pin(self):
        card = self.make_card(is_approved=False)
        self.grant_qr()
        self.assertEqual(self.client.post(self.url('approve_card', card_id=card.id)).status_code, 403)
        self.assertEqual(self.client.post(self.url('pin_card', card_id=card.id)).status_code, 403)
        card.refresh_from_db()
        self.assertFalse(card.is_approved)

    def test_pin_toggles(self):
        card = self.make_card()
        self.login_teacher()
        self.client.post(self.url('pin_card', card_id=card.id))
        card.refresh_from_db()
        self.assertTrue(card.is_pinned)
        self.assertContains(self.client.get(self.board_url()), 'Angeheftet')


class EduCardsInteractionTests(EduCardsTestCase):
    def test_like_toggle_for_view_only_guest(self):
        card = self.make_card()
        self.grant_qr(CardsPageAccessToken.ACCESS_VIEW)
        url = self.url('react_card', card_id=card.id)
        data = self.client.post(url).json()
        self.assertEqual(data, {'liked': True, 'count': 1})
        data = self.client.post(url).json()
        self.assertEqual(data, {'liked': False, 'count': 0})

    def test_likes_are_counted_per_person(self):
        card = self.make_card()
        self.grant_qr(CardsPageAccessToken.ACCESS_VIEW)
        self.client.post(self.url('react_card', card_id=card.id))
        other = self.client_class()
        other.login(username='teacher', password='password')
        self.assertEqual(other.post(self.url('react_card', card_id=card.id)).json()['count'], 2)

    def test_likes_can_be_disabled(self):
        self.page.allow_reactions = False
        self.page.save()
        card = self.make_card()
        self.login_teacher()
        self.assertEqual(self.client.post(self.url('react_card', card_id=card.id)).status_code, 403)
        self.assertNotContains(self.client.get(self.board_url()), 'data-ec-react')

    def test_like_requires_board_access(self):
        card = self.make_card()
        self.assertEqual(self.client.post(self.url('react_card', card_id=card.id)).status_code, 403)
        self.assertFalse(CardReaction.objects.exists())

    def test_guest_with_edit_access_can_comment_and_delete_own_comment(self):
        card = self.make_card()
        self.grant_qr()
        response = self.client.post(self.url('add_comment', card_id=card.id), {'text': 'Tolle Idee!', 'author_name': 'Ben'})
        self.assertRedirects(response, f'{self.board_url()}#card-{card.id}', fetch_redirect_response=False)
        comment = CardComment.objects.get()
        self.assertEqual(comment.author_name, 'Ben')
        self.assertContains(self.client.get(self.board_url()), 'Tolle Idee!')
        self.client.post(self.url('delete_comment', comment_id=comment.id))
        self.assertFalse(CardComment.objects.exists())

    def test_view_only_guest_cannot_comment(self):
        card = self.make_card()
        self.grant_qr(CardsPageAccessToken.ACCESS_VIEW)
        self.assertEqual(self.client.post(self.url('add_comment', card_id=card.id), {'text': 'Hi'}).status_code, 403)
        self.assertFalse(CardComment.objects.exists())

    def test_guest_cannot_delete_foreign_comment(self):
        card = self.make_card()
        comment = CardComment.objects.create(card=card, text='Teacher note', user=self.teacher)
        self.grant_qr()
        self.assertEqual(self.client.post(self.url('delete_comment', comment_id=comment.id)).status_code, 403)

    def test_comments_can_be_disabled(self):
        self.page.allow_comments = False
        self.page.save()
        card = self.make_card()
        self.login_teacher()
        self.assertEqual(self.client.post(self.url('add_comment', card_id=card.id), {'text': 'Hi'}).status_code, 403)

    def test_reorder_cards_across_columns(self):
        other = Category.objects.create(cards_page=self.page, name='Other', order=1)
        a, b, c = self.make_card(title='A', order=0), self.make_card(title='B', order=1), self.make_card(title='C', order=2)
        self.login_teacher()
        response = self.post_json(self.url('reorder_cards', page_id=self.page.id), {'category_id': other.id, 'card_ids': [c.id, a.id]})
        self.assertEqual(response.status_code, 200)
        a.refresh_from_db(); b.refresh_from_db(); c.refresh_from_db()
        self.assertEqual((a.category, a.order), (other, 1))
        self.assertEqual((c.category, c.order), (other, 0))
        self.assertEqual(b.category, self.category)

    def test_reorder_rejects_cards_from_other_boards(self):
        foreign_page = CardsPage.objects.create(title='Foreign', created_by=self.other_teacher)
        foreign_cat = Category.objects.create(cards_page=foreign_page, name='X')
        foreign_card = Card.objects.create(category=foreign_cat, title='Foreign card', content='x')
        self.login_teacher()
        self.post_json(self.url('reorder_cards', page_id=self.page.id), {'category_id': self.category.id, 'card_ids': [foreign_card.id]})
        foreign_card.refresh_from_db()
        self.assertEqual(foreign_card.category, foreign_cat)

    def test_reorder_requires_membership(self):
        card = self.make_card()
        self.grant_qr()
        response = self.post_json(self.url('reorder_cards', page_id=self.page.id), {'category_id': self.category.id, 'card_ids': [card.id]})
        self.assertEqual(response.status_code, 403)
        response = self.post_json(self.url('reorder_categories', page_id=self.page.id), {'category_ids': [self.category.id]})
        self.assertEqual(response.status_code, 403)

    def test_reorder_columns(self):
        second = Category.objects.create(cards_page=self.page, name='Second', order=1)
        self.login_teacher()
        response = self.post_json(self.url('reorder_categories', page_id=self.page.id), {'category_ids': [second.id, self.category.id]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.page.categories.order_by('order').values_list('name', flat=True)), ['Second', 'Test Column'])

    def test_state_version_changes_and_partial_renders_board(self):
        self.login_teacher()
        state_url = self.url('cards_page_state', page_id=self.page.id)
        before = self.client.get(state_url).json()['version']
        self.make_card(title='Fresh card')
        after = self.client.get(state_url).json()['version']
        self.assertNotEqual(before, after)
        response = self.client.get(self.board_url(), {'partial': '1'})
        self.assertTemplateUsed(response, 'eduCards/_board.html')
        self.assertTemplateNotUsed(response, 'eduCards/base_educards.html')
        self.assertContains(response, 'Fresh card')

    def test_state_requires_access(self):
        self.assertEqual(self.client.get(self.url('cards_page_state', page_id=self.page.id)).status_code, 403)


class EduCardsBoardManagementTests(EduCardsTestCase):
    def test_create_board_from_template(self):
        self.login_teacher()
        response = self.client.post(self.url('create_cards_page'), {
            'title': 'Kanban board', 'icon': '🚀', 'layout': 'grid', 'background': 'forest',
            'template': 'kanban', 'allow_reactions': 'on', 'allow_comments': 'on',
        })
        page = CardsPage.objects.get(title='Kanban board')
        self.assertRedirects(response, self.url('cards_page_detail', page_id=page.id))
        self.assertEqual(list(page.categories.order_by('order').values_list('name', flat=True)),
                         ['Zu erledigen', 'In Arbeit', 'Erledigt'])
        self.assertEqual(page.layout, 'grid')
        self.assertEqual(page.created_by, self.teacher)
        self.assertTrue(page.is_active)

    def test_board_settings_are_rendered(self):
        self.page.layout = 'stream'
        self.page.background = 'sunset'
        self.page.save()
        self.login_teacher()
        response = self.client.get(self.board_url())
        self.assertContains(response, 'layout-stream')
        self.assertContains(response, '#ff7e5f')

    def test_duplicate_board(self):
        self.make_card(title='Keep me', color='green')
        self.make_card(title='Pending', is_approved=False)
        CardsPageAccessToken.objects.create(cards_page=self.page, token='abc', created_by=self.teacher)
        self.page.shared_with.add(self.other_teacher)
        self.login_teacher('other_teacher')
        self.client.post(self.url('duplicate_cards_page', page_id=self.page.id))
        copy = CardsPage.objects.get(title='Kopie von Test Page')
        self.assertEqual(copy.created_by, self.other_teacher)
        self.assertEqual(copy.categories.count(), 1)
        self.assertEqual(list(Card.objects.filter(category__cards_page=copy).values_list('title', 'color')), [('Keep me', 'green')])
        self.assertFalse(copy.access_tokens.exists())

    def test_archive_and_restore(self):
        self.login_teacher()
        self.client.post(self.url('toggle_archive_cards_page', page_id=self.page.id))
        self.page.refresh_from_db()
        self.assertFalse(self.page.is_active)
        response = self.client.get(self.url('cards_page_list'))
        self.assertContains(response, 'Archiv')
        self.assertContains(response, 'Wiederherstellen')
        # members can still open archived boards, guests can't
        self.assertEqual(self.client.get(self.board_url()).status_code, 200)
        guest = self.client_class()
        self.assertEqual(guest.get(self.board_url()).status_code, 404)
        self.client.post(self.url('toggle_archive_cards_page', page_id=self.page.id))
        self.page.refresh_from_db()
        self.assertTrue(self.page.is_active)

    def test_board_list_search(self):
        CardsPage.objects.create(title='Mathe Brainstorming', created_by=self.teacher)
        self.login_teacher()
        response = self.client.get(self.url('cards_page_list'), {'q': 'mathe'})
        self.assertContains(response, 'Mathe Brainstorming')
        self.assertNotContains(response, 'Test Page')

    def test_duplicate_column_name_is_rejected(self):
        self.login_teacher()
        response = self.client.post(self.url('create_category', page_id=self.page.id), {'name': 'test column', 'color': '#000000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bereits eine Spalte')
        self.assertEqual(self.page.categories.count(), 1)

    def test_new_column_is_appended(self):
        self.login_teacher()
        self.client.post(self.url('create_category', page_id=self.page.id), {'name': 'Neu', 'color': '#1c7ed6'})
        self.assertEqual(list(self.page.categories.order_by('order').values_list('name', flat=True)), ['Test Column', 'Neu'])

    def test_guest_board_list_shows_qr_boards(self):
        self.grant_qr(CardsPageAccessToken.ACCESS_VIEW)
        self.assertContains(self.client.get(self.url('cards_page_list')), 'Test Page')

    def test_share_page_renders_qr(self):
        CardsPageAccessToken.objects.create(cards_page=self.page, token='abc', created_by=self.teacher)
        self.login_teacher()
        response = self.client.get(self.url('share_cards_page', page_id=self.page.id))
        self.assertContains(response, 'data:image/png;base64,')
        self.assertContains(response, '/educards/page/%d/access/abc/' % self.page.id)


class SanitizerTests(TestCase):
    def test_keeps_editor_formatting(self):
        html = ('<h2>Titel</h2><p><strong>fett</strong> <i>kursiv</i> <span style="color:#ff0000;">rot</span></p>'
                '<ul><li>a</li></ul><a href="https://example.org">Link</a>')
        cleaned = sanitize_html(html)
        for fragment in ('<h2>Titel</h2>', '<strong>fett</strong>', 'style="color:#ff0000"', '<li>a</li>', 'href="https://example.org"'):
            self.assertIn(fragment, cleaned)
        self.assertIn('rel="noopener noreferrer nofollow"', cleaned)

    def test_removes_dangerous_markup(self):
        cleaned = sanitize_html(
            '<script>alert(1)</script><iframe src="https://evil"></iframe>'
            '<p onmouseover="x()" style="background:url(javascript:x)">ok</p>'
            '<a href="javascript:alert(1)">a</a><a href="data:text/html,x">b</a><img src=x onerror=alert(1)>'
        )
        for bad in ('script', 'iframe', 'onmouseover', 'url(', 'javascript', 'data:', '<img', 'onerror'):
            self.assertNotIn(bad, cleaned)
        self.assertIn('ok', cleaned)

    def test_escapes_text_and_closes_tags(self):
        self.assertEqual(sanitize_html('<p>1 < 2 & <b>x'), '<p>1 &lt; 2 &amp; <b>x</b></p>')


class EmptyRichTextTests(EduCardsTestCase):
    def test_empty_editor_fields_are_stored_empty(self):
        self.login_teacher()
        self.client.post(self.url('create_card', category_id=self.category.id),
                         {'title': 'Link only', 'content': '<p>&nbsp;</p>', 'additional_info': '<p>\xa0</p>',
                          'link_url': 'https://example.org'})
        card = Card.objects.get(title='Link only')
        self.assertEqual(card.content, '')
        self.assertEqual(card.additional_info, '')
        self.assertNotContains(self.client.get(self.board_url()), 'Mehr anzeigen')


class DemoCommandTests(EduCardsTestCase):
    def call(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('educards_demo', *args, stdout=out)
        return out.getvalue()

    def test_creates_boards_for_existing_teacher_and_is_idempotent(self):
        output = self.call('--owner', 'teacher')
        self.assertIn('4 Demo-Board(s)', output)
        boards = CardsPage.objects.filter(created_by=self.teacher).exclude(pk=self.page.pk)
        self.assertEqual(boards.count(), 4)
        climate = boards.get(title='Projektwoche Klimawandel')
        self.assertTrue(climate.require_approval)
        self.assertEqual(climate.categories.count(), 4)
        self.assertTrue(Card.objects.filter(category__cards_page=climate, is_approved=False).exists())
        self.assertTrue(CardAttachment.objects.filter(card__category__cards_page=climate).count() >= 2)
        self.assertTrue(climate.access_tokens.exists())
        self.assertFalse(User.objects.filter(username='demo_lehrkraft').exists())

        self.assertIn('Übersprungen', self.call('--owner', 'teacher'))
        self.assertEqual(boards.count(), 4)

        self.call('--owner', 'teacher', '--reset')
        self.assertEqual(boards.count(), 4)
        self.assertTrue(CardsPage.objects.filter(pk=self.page.pk).exists())

        self.login_teacher()
        response = self.client.get(self.url('cards_page_detail', page_id=boards.get(title='Projektwoche Klimawandel').id))
        self.assertContains(response, 'Gletscherschmelze')
        self.assertContains(response, 'pdfjs-preview')

    def test_reset_keeps_teachers_own_board_with_same_title(self):
        own = CardsPage.objects.create(title='Mathe-Fragen 7b', description='Meine echte Klasse', created_by=self.teacher)
        self.call('--owner', 'teacher')
        self.call('--owner', 'teacher', '--reset')
        self.assertTrue(CardsPage.objects.filter(pk=own.pk).exists())
        self.assertEqual(CardsPage.objects.filter(title='Mathe-Fragen 7b').count(), 2)

    def test_rejects_unknown_or_non_teacher_owner(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.call('--owner', 'nobody')
        with self.assertRaises(CommandError):
            self.call('--owner', 'student')

    @override_settings(DEBUG=False)
    def test_demo_accounts_only_with_debug(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.call()

    @override_settings(DEBUG=True)
    def test_creates_demo_accounts(self):
        output = self.call()
        teacher = User.objects.get(username='demo_lehrkraft')
        colleague = User.objects.get(username='demo_kollege')
        self.assertFalse(teacher.is_staff)
        self.assertTrue(teacher.groups.filter(name='teachers').exists())
        self.assertIn('demo_lehrkraft / ', output)
        self.assertTrue(CardsPage.objects.get(title='Projektwoche Klimawandel').shared_with.filter(pk=colleague.pk).exists())
        # second run doesn't print a new password
        self.assertNotIn('demo_lehrkraft / ', self.call())
