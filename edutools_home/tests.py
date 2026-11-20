from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import UserProfile
from WLANCodesWebApp.models import Config

from .models import DEFAULT_REGISTRATION_MAIL_TEXT, EdutoolsSetting


class UserProfileDeleteTests(TestCase):
	def setUp(self):
		self.staff = User.objects.create_user(
			username="admin", password="password", is_staff=True
		)
		self.client.force_login(self.staff)

	def test_delete_removes_profile_and_linked_user(self):
		user = User.objects.create_user(username="teacher")
		profile = UserProfile.objects.create(
			user=user, abbr="TCH", email="teacher@example.com"
		)

		response = self.client.post(f"/userprofile_delete/{profile.id}/")

		self.assertRedirects(response, "/userprofiles/")
		self.assertFalse(UserProfile.objects.filter(pk=profile.pk).exists())
		self.assertFalse(User.objects.filter(pk=user.pk).exists())

	def test_delete_removes_profile_without_linked_user(self):
		profile = UserProfile.objects.create(abbr="TCH", email="teacher@example.com")

		response = self.client.post(f"/userprofile_delete/{profile.id}/")

		self.assertRedirects(response, "/userprofiles/")
		self.assertFalse(UserProfile.objects.filter(pk=profile.pk).exists())

	def test_add_page_renders_without_persisted_profile(self):
		response = self.client.get("/userprofile_add/")

		self.assertEqual(response.status_code, 200)

# Create your tests here.


class RegistrationMailTextMigrationTests(TestCase):
	"""Tests for the data migration that moves the registration mail text."""

	def run_migration(self):
		import importlib

		from django.apps import apps

		module = importlib.import_module(
			"edutools_home.migrations.0005_move_registration_mail_text"
		)
		module.move_registration_mail_text(apps, None)

	def test_fresh_database_contains_default_text(self):
		# the migrations ran when the test database was created
		setting = EdutoolsSetting.objects.get(name="settings")

		self.assertEqual(setting.registration_mail_text, DEFAULT_REGISTRATION_MAIL_TEXT)
		self.assertIn("#LINK#", setting.registration_mail_text)

	def test_existing_text_is_moved_from_config(self):
		EdutoolsSetting.objects.all().delete()
		Config.objects.create(name="accounts_mail_text", text="Eigener Text: #LINK#")

		self.run_migration()

		setting = EdutoolsSetting.objects.get(name="settings")
		self.assertEqual(setting.registration_mail_text, "Eigener Text: #LINK#")
		self.assertFalse(Config.objects.filter(name="accounts_mail_text").exists())

	def test_existing_settings_keep_other_fields(self):
		EdutoolsSetting.objects.filter(name="settings").update(
			login_hint="Hinweis", registration_mail_text=""
		)
		Config.objects.create(name="accounts_mail_text", text="   ")

		self.run_migration()

		setting = EdutoolsSetting.objects.get(name="settings")
		self.assertEqual(setting.login_hint, "Hinweis")
		self.assertEqual(setting.registration_mail_text, DEFAULT_REGISTRATION_MAIL_TEXT)
		self.assertEqual(EdutoolsSetting.objects.count(), 1)
