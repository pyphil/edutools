from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import UserProfile


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
