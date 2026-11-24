import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import QRCodeModel


class GetQRImageTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root)
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        os.makedirs(os.path.join(self.media_root, 'qr_codes'))
        with open(os.path.join(self.media_root, 'qr_codes', 'code.png'), 'wb') as f:
            f.write(b'png')

        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='x')
        self.other = User.objects.create_user(username='other', password='x')
        QRCodeModel.objects.create(image='qr_codes/code.png', url='https://example.com', user=self.owner)

    def test_owner_can_view(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('get_qr_image', args=['code.png']))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('attachment', response.get('Content-Disposition', ''))
        self.assertEqual(b''.join(response.streaming_content), b'png')

    def test_owner_can_download(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('get_qr_image', args=['code.png']) + '?attach=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('get_qr_image', args=['code.png']))
        self.assertEqual(response.status_code, 404)

    def test_unknown_code_gets_404(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('get_qr_image', args=['nope.png']))
        self.assertEqual(response.status_code, 404)

    def test_record_without_file_gets_404(self):
        QRCodeModel.objects.create(image='qr_codes/gone.png', url='https://example.com', user=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get(reverse('get_qr_image', args=['gone.png']))
        self.assertEqual(response.status_code, 404)
