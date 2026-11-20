import re
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from WLANCodesWebApp.models import Config
from edutools_home.models import DEFAULT_REGISTRATION_MAIL_TEXT, EdutoolsSetting

from .models import RegistrationID, UserProfile

PASSWORD = 'S3hrGeheim!x'
HOST = 'edutools.example.org'


@override_settings(ALLOWED_HOSTS=[HOST], EMAIL_LINKS_USE_HTTPS=True, DEFAULT_FROM_EMAIL='')
class AccountsTestCase(TestCase):
    def setUp(self):
        # rate limit counters live in the cache
        cache.clear()
        self.client.defaults['HTTP_HOST'] = HOST

    def create_mail_config(self, text='Hier ist dein Link: #LINK#', sender='noreply@example.org'):
        EdutoolsSetting.objects.update_or_create(name='settings', defaults={'registration_mail_text': text})
        Config.objects.create(name='noreply-mail', setting=sender)


class EmailCheckTests(AccountsTestCase):
    url = reverse('email_check')

    def setUp(self):
        super().setUp()
        self.create_mail_config()
        UserProfile.objects.create(abbr='mus', email='Max.Muster@Schule.de')

    def test_sends_registration_mail_with_https_link(self):
        response = self.client.post(self.url, {'mail': ' max.muster@schule.de '})

        self.assertRedirects(response, reverse('registration_email'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['max.muster@schule.de'])
        self.assertEqual(message.from_email, 'noreply@example.org')
        registration = RegistrationID.objects.get()
        self.assertEqual(registration.user_email, 'max.muster@schule.de')
        self.assertIn(f'https://{HOST}/accounts/register/{registration.uuid}/', message.body)

    def test_new_request_invalidates_old_link(self):
        self.client.post(self.url, {'mail': 'max.muster@schule.de'})
        old_uuid = RegistrationID.objects.get().uuid
        self.client.post(self.url, {'mail': 'Max.Muster@schule.de'})

        self.assertEqual(RegistrationID.objects.count(), 1)
        self.assertNotEqual(RegistrationID.objects.get().uuid, old_uuid)

    def test_unknown_email_not_allowed(self):
        response = self.client.post(self.url, {'mail': 'fremd@schule.de'})

        self.assertEqual(response.context['email_error'], 'not_allowed')
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_mail_field_does_not_crash(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['email_error'], 'not_allowed')

    def test_already_used_is_case_insensitive(self):
        User.objects.create_user('max', 'Max.Muster@Schule.de', PASSWORD)
        response = self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(response.context['email_error'], 'already_used')
        self.assertEqual(len(mail.outbox), 0)

    def test_smtp_error_is_shown_and_logged(self):
        with mock.patch('accounts.views.send_mail', side_effect=OSError('SMTP down')), \
                self.assertLogs('accounts', level='ERROR'):
            response = self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(response.context['email_error'], 'mail_failed')
        self.assertFalse(RegistrationID.objects.exists())

    def test_missing_link_placeholder_is_reported(self):
        EdutoolsSetting.objects.filter(name='settings').update(registration_mail_text='Text ohne Link')
        with self.assertLogs('accounts', level='ERROR'):
            response = self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(response.context['email_error'], 'mail_failed')
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_settings_are_reported(self):
        EdutoolsSetting.objects.all().delete()
        with self.assertLogs('accounts', level='ERROR'):
            response = self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(response.context['email_error'], 'mail_failed')

    def test_missing_sender_is_reported(self):
        Config.objects.filter(name='noreply-mail').delete()
        with self.assertLogs('accounts', level='ERROR'):
            response = self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(response.context['email_error'], 'mail_failed')
        self.assertEqual(len(mail.outbox), 0)

    def test_default_text_is_used(self):
        EdutoolsSetting.objects.filter(name='settings').update(
            registration_mail_text=DEFAULT_REGISTRATION_MAIL_TEXT)
        self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        body = mail.outbox[0].body
        self.assertNotIn('#LINK#', body)
        self.assertIn('48 Stunden gültig', body)
        self.assertIn(f'https://{HOST}/accounts/register/{RegistrationID.objects.get().uuid}/', body)

    @override_settings(DEFAULT_FROM_EMAIL='fallback@example.org')
    def test_sender_falls_back_to_default_from_email(self):
        Config.objects.filter(name='noreply-mail').delete()
        self.client.post(self.url, {'mail': 'max.muster@schule.de'})

        self.assertEqual(mail.outbox[0].from_email, 'fallback@example.org')

    def test_rate_limit_per_email(self):
        for _ in range(3):
            self.client.post(self.url, {'mail': 'max.muster@schule.de'})
        response = self.client.post(self.url, {'mail': 'MAX.MUSTER@schule.de'})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 3)


class RegisterTests(AccountsTestCase):
    def setUp(self):
        super().setUp()
        self.profile = UserProfile.objects.create(abbr='mus', email='Max.Muster@Schule.de')
        self.registration = RegistrationID.objects.create(
            user_email='max.muster@schule.de', uuid='a' * 32
        )
        self.url = reverse('register', args=[self.registration.uuid])

    def post(self, url=None, **extra):
        data = {'username': 'max', 'email': 'max.muster@schule.de',
                'password1': PASSWORD, 'password2': PASSWORD}
        data.update(extra)
        return self.client.post(url or self.url, data)

    def test_successful_registration(self):
        response = self.post()

        self.assertRedirects(response, reverse('account_success'))
        user = User.objects.get(username='max')
        self.assertEqual(user.email, 'max.muster@schule.de')
        self.assertTrue(user.groups.filter(name='teachers').exists())
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.user, user)
        self.assertFalse(RegistrationID.objects.exists())

    def test_invalid_link_does_not_create_user(self):
        UserProfile.objects.create(abbr='kol', email='kollege@schule.de')
        response = self.post(url=reverse('register', args=['beliebig']), email='kollege@schule.de')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['link_error'])
        self.assertFalse(User.objects.exists())

    def test_posted_email_is_ignored(self):
        other = UserProfile.objects.create(abbr='kol', email='kollege@schule.de')
        self.post(email='kollege@schule.de')

        user = User.objects.get(username='max')
        self.assertEqual(user.email, 'max.muster@schule.de')
        other.refresh_from_db()
        self.assertIsNone(other.user)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.user, user)

    def test_expired_link_is_rejected(self):
        RegistrationID.objects.filter(pk=self.registration.pk).update(
            created=timezone.now() - timedelta(hours=49)
        )
        response = self.post()

        self.assertTrue(response.context['link_error'])
        self.assertFalse(User.objects.exists())

    def test_get_shows_email_from_link(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context['user_email'], 'max.muster@schule.de')
        self.assertFalse(response.context['link_error'])

    def test_already_registered_email(self):
        User.objects.create_user('alt', 'MAX.MUSTER@schule.de', PASSWORD)
        response = self.post()

        self.assertEqual(response.context['email_error'], 'already_used')
        self.assertFalse(User.objects.filter(username='max').exists())

    def test_profile_already_linked(self):
        self.profile.user = User.objects.create_user('alt', 'alt@schule.de', PASSWORD)
        self.profile.save()
        response = self.post()

        self.assertEqual(response.context['email_error'], 'already_used')
        self.assertFalse(User.objects.filter(username='max').exists())

    def test_profile_removed_meanwhile(self):
        self.profile.delete()
        response = self.post()

        self.assertEqual(response.context['email_error'], 'not_allowed')
        self.assertFalse(User.objects.exists())

    def test_invalid_form_creates_nothing(self):
        response = self.post(password2='anders')

        self.assertTrue(response.context['form'].errors)
        self.assertFalse(User.objects.exists())
        self.assertTrue(RegistrationID.objects.exists())

    def test_error_while_linking_profile_rolls_back_user(self):
        with mock.patch.object(UserProfile, 'save', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                self.post()

        self.assertFalse(User.objects.exists())
        self.assertTrue(RegistrationID.objects.exists())


class PasswordResetTests(AccountsTestCase):
    url = reverse('password_reset')

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('max', 'max.muster@schule.de', PASSWORD)

    def test_reset_mail_uses_configured_sender_and_https(self):
        self.create_mail_config()
        response = self.client.post(self.url, {'email': 'MAX.Muster@schule.de'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, 'noreply@example.org')
        self.assertEqual(message.to, ['max.muster@schule.de'])
        self.assertRegex(message.body, rf'https://{re.escape(HOST)}/accounts/reset/[^/]+/[^/]+/')
        self.assertIn('max', message.body)

    @override_settings(DEFAULT_FROM_EMAIL='fallback@example.org')
    def test_reset_sender_falls_back_to_default_from_email(self):
        self.client.post(self.url, {'email': 'max.muster@schule.de'})

        self.assertEqual(mail.outbox[0].from_email, 'fallback@example.org')

    def test_missing_sender_is_logged(self):
        with self.assertLogs('accounts', level='ERROR'):
            self.client.post(self.url, {'email': 'max.muster@schule.de'})

    def test_reset_link_works(self):
        self.create_mail_config()
        self.client.post(self.url, {'email': 'max.muster@schule.de'})
        link = re.search(r'https://[^/]+(/accounts/reset/\S+)', mail.outbox[0].body).group(1)

        response = self.client.get(link, follow=True)
        self.assertTrue(response.context['validlink'])
        response = self.client.post(response.redirect_chain[-1][0], {
            'new_password1': 'N3uesPasswort!y', 'new_password2': 'N3uesPasswort!y'})
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('N3uesPasswort!y'))

    def test_unknown_email_gives_same_response(self):
        self.create_mail_config()
        response = self.client.post(self.url, {'email': 'gibtsnicht@schule.de'})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_smtp_error_is_logged(self):
        self.create_mail_config()
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('SMTP down')), \
                self.assertLogs('django.contrib.auth', level='ERROR'):
            response = self.client.post(self.url, {'email': 'max.muster@schule.de'})

        self.assertRedirects(response, reverse('password_reset_done'))

    def test_rate_limit_per_email(self):
        self.create_mail_config()
        for _ in range(3):
            self.client.post(self.url, {'email': 'max.muster@schule.de'})
        response = self.client.post(self.url, {'email': 'Max.Muster@schule.de'})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 3)

    def test_rate_limit_per_ip(self):
        self.create_mail_config()
        for i in range(10):
            self.client.post(self.url, {'email': f'person{i}@schule.de'})
        response = self.client.post(self.url, {'email': 'max.muster@schule.de'})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 0)

    def test_complete_page_links_to_login(self):
        response = self.client.get(reverse('password_reset_complete'))

        self.assertContains(response, f'href="{reverse("login")}"')
