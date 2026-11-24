from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Activity, ActivityBlock, ActivitySetting


class ManageBlocksAndActivitiesRedirectTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='x', is_staff=True)
        self.client.force_login(self.user)
        ActivitySetting.objects.create(title='Titel')
        self.url = reverse('manage_blocks_and_activities')

    def post(self, data):
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        return response['Location']

    def test_save_title_redirects_to_manage_page(self):
        self.assertEqual(self.post({'save_title': '1', 'title': 'Neu'}), self.url)

    def test_block_redirects(self):
        self.assertEqual(self.post({'add_block': '1', 'name': ''}), self.url)
        location = self.post({'add_block': '1', 'name': 'Block A', 'order': 1})
        block = ActivityBlock.objects.get(name='Block A')
        self.assertEqual(location, f'{self.url}#block-{block.id}')
        location = self.post({'save_block': '1', 'block_id': block.id, 'name': 'Block B', 'order': 1})
        self.assertEqual(location, f'{self.url}#block-{block.id}')
        location = self.post({'delete_block': '1', 'block_id': block.id})
        self.assertEqual(location, f'{self.url}#block-list')

    def test_activity_redirects(self):
        self.assertEqual(self.post({'add_activity': '1', 'name': ''}), self.url)
        location = self.post({'add_activity': '1', 'name': 'Act A', 'order': 1})
        activity = Activity.objects.get(name='Act A')
        self.assertEqual(location, f'{self.url}#activity-{activity.id}')
        location = self.post({'save_activity': '1', 'activity_id': activity.id, 'name': 'Act B', 'order': 1})
        self.assertEqual(location, f'{self.url}#activity-{activity.id}')
        location = self.post({'delete_activity': '1', 'activity_id': activity.id})
        self.assertEqual(location, f'{self.url}#activity-list')
