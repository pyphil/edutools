from datetime import date, time, timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from WLANCodesWebApp.models import Config

from .forms import AppointmentForm
from .models import Appointment, AppointmentMail, AppointmentSetting

FUTURE = timezone.localdate() + timedelta(days=7)
PAST = timezone.localdate() - timedelta(days=7)


def booking_data(**overrides):
    data = {
        'student_name': 'Max Muster',
        'primary_school': 'GGS Am Park',
        'parents_name': 'Erika Muster',
        'email': 'eltern@example.org',
        'email_2': 'eltern@example.org',
        'phone': '02428 / 123-45',
        'website': '',
    }
    data.update(overrides)
    return data


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AppointmentTestCase(TestCase):
    def setUp(self):
        cache.clear()
        Config.objects.create(name='noreply-mail', setting='noreply@schule.example')
        AppointmentMail.objects.create(
            mail_text='Termin für #KIND# am #DATUM# um #UHRZEIT#',
            mail_text_reminder='Erinnerung: #KIND# am #DATUM# um #UHRZEIT#',
        )
        AppointmentSetting.objects.create(title='Anmeldung', show_empty_days=True,
                                          privacy_notice='Ihre Daten werden nach dem Termin gelöscht.')
        self.slot = Appointment.objects.create(date=FUTURE, time=time(10, 0))

    def make_admin(self):
        user = User.objects.create_user('sekretariat', password='pw')
        user.groups.add(Group.objects.create(name='appointment_admin'))
        self.client.force_login(user)
        return user

    def book(self, slot=None, **overrides):
        slot = slot or self.slot
        return self.client.post(reverse('book_appointment', args=[slot.id]), booking_data(**overrides))


class PublicBookingTests(AppointmentTestCase):
    def test_list_shows_free_future_slots_only(self):
        Appointment.objects.create(date=PAST, time=time(10, 0))
        booked = Appointment.objects.create(date=FUTURE, time=time(11, 0), student_name='X', email='x@example.org')
        hidden = Appointment.objects.create(date=FUTURE, time=time(12, 0), visible=False)
        response = self.client.get(reverse('appointment'))
        self.assertEqual(response.status_code, 200)
        items = response.context['appointment_items']
        self.assertEqual([d for d, _ in items], [FUTURE])
        self.assertEqual(list(items[0][1]), [self.slot])
        self.assertNotIn(booked, items[0][1])
        self.assertNotIn(hidden, items[0][1])

    def test_successful_booking_saves_data_and_sends_mail(self):
        response = self.book()
        self.assertRedirects(response, reverse('success_appointment'), fetch_redirect_response=False)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.student_name, 'Max Muster')
        self.assertEqual(self.slot.email, 'eltern@example.org')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['eltern@example.org'])
        self.assertEqual(mail.outbox[0].from_email, 'noreply@schule.example')
        self.assertIn('Max Muster', mail.outbox[0].body)

        success = self.client.get(reverse('success_appointment'))
        self.assertContains(success, 'Max Muster')
        # the success page can only be shown once
        self.assertRedirects(self.client.get(reverse('success_appointment')), reverse('appointment'))

    def test_booking_form_shows_privacy_notice(self):
        response = self.client.get(reverse('book_appointment', args=[self.slot.id]))
        self.assertContains(response, 'Ihre Daten werden nach dem Termin gelöscht.')

    def test_email_is_normalized(self):
        self.book(email=' Eltern@Example.org ', email_2='eltern@example.ORG')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.email, 'eltern@example.org')

    def test_email_mismatch_is_rejected(self):
        response = self.book(email_2='andere@example.org')
        self.assertEqual(response.status_code, 200)
        self.assertIn('email_2', response.context['form'].errors)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)
        self.assertEqual(len(mail.outbox), 0)

    def test_links_and_markup_in_names_are_rejected(self):
        for value in ('https://evil.example', 'www.evil.example', '<script>', 'a@b.de'):
            response = self.book(student_name=value)
            self.assertIn('student_name', response.context['form'].errors, value)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)

    def test_regular_names_are_accepted(self):
        response = self.book(student_name="Anna-Lena O'Brien Müller", primary_school='KGS St. Josef, Merzenich')
        self.assertRedirects(response, reverse('success_appointment'))

    def test_invalid_phone_is_rejected(self):
        response = self.book(phone='call me maybe')
        self.assertIn('phone', response.context['form'].errors)

    def test_honeypot_blocks_booking(self):
        response = self.book(website='http://spam.example')
        self.assertEqual(response.status_code, 200)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)

    def test_booked_slot_cannot_be_overwritten_and_data_is_not_leaked(self):
        self.book()
        response = self.book(student_name='Eva Zweite', parents_name='Paul Zweite', email='zwei@example.org',
                             email_2='zwei@example.org')
        self.assertEqual(response.context['alert'], 'booked')
        self.assertNotContains(response, 'Max Muster')
        self.assertNotContains(response, 'eltern@example.org')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.student_name, 'Max Muster')

    def test_get_on_booked_slot_redirects(self):
        self.book()
        self.assertRedirects(self.client.get(reverse('book_appointment', args=[self.slot.id])),
                             reverse('appointment'))

    def test_concurrent_booking_does_not_overwrite(self):
        """Another family books the slot between the availability check and the save."""
        original = AppointmentForm.personal_data

        def book_in_between(form):
            Appointment.objects.filter(pk=self.slot.pk).update(student_name='Schneller', email='s@example.org')
            return original(form)

        with mock.patch.object(AppointmentForm, 'personal_data', book_in_between):
            response = self.book()
        self.assertEqual(response.context['alert'], 'booked')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.student_name, 'Schneller')
        self.assertEqual(len(mail.outbox), 0)

    def test_hidden_and_past_slots_cannot_be_booked(self):
        hidden = Appointment.objects.create(date=FUTURE, time=time(9, 0), visible=False)
        past = Appointment.objects.create(date=PAST, time=time(9, 0))
        for slot in (hidden, past):
            self.assertEqual(self.book(slot).context['alert'], 'booked')
            slot.refresh_from_db()
            self.assertFalse(slot.is_booked)

    def test_unknown_slot_returns_404(self):
        self.assertEqual(self.client.get(reverse('book_appointment', args=[99999])).status_code, 404)

    def test_rate_limit_per_email(self):
        slots = [Appointment.objects.create(date=FUTURE, time=time(13, i)) for i in range(4)]
        for slot in slots[:3]:
            self.assertRedirects(self.book(slot), reverse('success_appointment'))
        response = self.book(slots[3])
        self.assertEqual(response.status_code, 429)
        slots[3].refresh_from_db()
        self.assertFalse(slots[3].is_booked)

    def test_invalid_attempts_do_not_count_against_email_limit(self):
        for _ in range(5):
            self.book(phone='invalid!')
        self.assertRedirects(self.book(), reverse('success_appointment'))

    def test_booking_works_without_mail_configuration(self):
        Config.objects.all().delete()
        AppointmentMail.objects.all().delete()
        with self.settings(DEFAULT_FROM_EMAIL=''):
            response = self.book()
        self.assertRedirects(response, reverse('success_appointment'), fetch_redirect_response=False)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)
        self.assertEqual(self.client.get(reverse('success_appointment')).status_code, 200)

    def test_success_page_without_session_redirects(self):
        self.assertRedirects(self.client.get(reverse('success_appointment')), reverse('appointment'))


class AdminAccessTests(AppointmentTestCase):
    admin_urls = ['create_appointment', 'appointment_admin', 'appointment_email', 'appointment_settings',
                  'delete_past_appointments']

    def test_anonymous_is_redirected_to_login(self):
        for name in self.admin_urls:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn('login', response.url)

    def test_staff_without_group_has_no_access(self):
        user = User.objects.create_user('lehrer', password='pw', is_staff=True)
        self.client.force_login(user)
        for name in self.admin_urls:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

    def test_group_member_and_superuser_have_access(self):
        self.make_admin()
        for name in self.admin_urls:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.client.force_login(User.objects.create_superuser('root', password='pw'))
        self.assertEqual(self.client.get(reverse('appointment_admin')).status_code, 200)


class AdminFunctionTests(AppointmentTestCase):
    def setUp(self):
        super().setUp()
        self.make_admin()

    def test_create_appointments(self):
        response = self.client.post(reverse('create_appointment'), {
            'date': FUTURE.isoformat(), 'start_time': '08:30', 'interval': '20', 'number': '3', 'slots': '2',
            'visible': 'on',
        })
        self.assertRedirects(response, reverse('appointment'))
        times = list(Appointment.objects.filter(date=FUTURE).exclude(pk=self.slot.pk)
                     .order_by('time').values_list('time', flat=True))
        self.assertEqual(times, [time(8, 30)] * 2 + [time(8, 50)] * 2 + [time(9, 10)] * 2)

    def test_create_appointments_rejects_invalid_input(self):
        for data in ({'date': 'x', 'start_time': '08:00', 'interval': '10', 'number': '1', 'slots': '1'},
                     {'date': FUTURE.isoformat(), 'start_time': '08:00', 'interval': '10', 'number': '100000',
                      'slots': '1'},
                     {'date': FUTURE.isoformat(), 'start_time': 'abc', 'interval': '', 'number': '1', 'slots': '1'}):
            response = self.client.post(reverse('create_appointment'), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_admin_page_with_invalid_date_does_not_crash(self):
        response = self.client.get(reverse('appointment_admin') + '?select=kaputt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_date'], FUTURE)

    def test_toggle_visibility(self):
        self.client.post(reverse('appointment_admin'), {'visible_id': self.slot.id})
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.visible)
        self.assertEqual(self.client.post(reverse('appointment_admin'), {'visible_id': 99999}).status_code, 404)
        self.client.post(reverse('appointment_admin'),
                         {'toggle_day': '1', 'select': FUTURE.isoformat()})
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.visible)

    def test_admin_can_book_hidden_slot_and_edit_booking(self):
        self.slot.visible = False
        self.slot.save()
        self.assertRedirects(self.book(), reverse('success_appointment'))
        response = self.client.get(reverse('edit_appointment', args=[self.slot.id]))
        self.assertEqual(response.context['form']['email_2'].value(), 'eltern@example.org')
        response = self.client.post(reverse('edit_appointment', args=[self.slot.id]),
                                    booking_data(parents_name='Erika und Hans Muster'))
        self.assertEqual(response.status_code, 302)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.parents_name, 'Erika und Hans Muster')

    def test_empty_slot_removes_personal_data(self):
        self.book()
        self.client.post(reverse('delete_appointment', args=[self.slot.id]), {'empty': '1'})
        self.slot.refresh_from_db()
        for field in Appointment.PERSONAL_FIELDS:
            self.assertEqual(getattr(self.slot, field), '')
        self.assertTrue(self.slot.visible)

    def test_reminder_only_for_upcoming_bookings(self):
        Appointment.objects.create(date=PAST, time=time(9, 0), student_name='Alt', email='alt@example.org')
        Appointment.objects.create(date=FUTURE, time=time(9, 0), student_name='Neu', email='neu@example.org')
        response = self.client.post(reverse('appointment_email'), {
            'mail_text': 'Termin #KIND#', 'mail_text_reminder': 'Erinnerung #KIND#', 'send_reminder': '1',
        })
        self.assertRedirects(response, reverse('appointment_email'))
        self.assertEqual([m.to for m in mail.outbox], [['neu@example.org']])

    def test_delete_past_appointments(self):
        Appointment.objects.create(date=PAST, time=time(9, 0), student_name='Alt', email='alt@example.org')
        response = self.client.get(reverse('delete_past_appointments'))
        self.assertEqual(response.context['count'], 1)
        self.client.post(reverse('delete_past_appointments'))
        self.assertEqual(list(Appointment.objects.all()), [self.slot])


class ManagementCommandTests(TestCase):
    def test_delete_past_appointments_command(self):
        today = timezone.localdate()
        old = Appointment.objects.create(date=today - timedelta(days=40), time=time(9, 0), student_name='Alt')
        recent = Appointment.objects.create(date=today - timedelta(days=5), time=time(9, 0), student_name='Neu')
        out = StringIO()
        call_command('delete_past_appointments', '--dry-run', stdout=out)
        self.assertTrue(Appointment.objects.filter(pk=old.pk).exists())
        call_command('delete_past_appointments', '--days', '30', stdout=out)
        self.assertEqual(list(Appointment.objects.all()), [recent])
