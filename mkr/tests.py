import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase, override_settings
from django.urls import reverse

from edutools_site.file_utils import safe_media_path


class MediaFileTestMixin:
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        for subdir in ('downloads', 'images', 'logo'):
            os.makedirs(os.path.join(self.media_root, subdir))
            with open(os.path.join(self.media_root, subdir, 'file.txt'), 'wb') as f:
                f.write(subdir.encode())
        with open(os.path.join(self.media_root, 'secret.txt'), 'wb') as f:
            f.write(b'secret')


class SafeMediaPathTests(MediaFileTestMixin, TestCase):
    def test_returns_path_inside_subdir(self):
        path = safe_media_path('images', 'file.txt')
        self.assertEqual(path, os.path.realpath(os.path.join(self.media_root, 'images', 'file.txt')))

    def test_rejects_traversal(self):
        for name in ('../secret.txt', '../../etc/passwd', '..', '.', ''):
            with self.subTest(name=name):
                with self.assertRaises(Http404):
                    safe_media_path('images', name)

    def test_rejects_absolute_path(self):
        with self.assertRaises(Http404):
            safe_media_path('images', os.path.join(self.media_root, 'secret.txt'))

    def test_rejects_sibling_dir_with_common_prefix(self):
        os.makedirs(os.path.join(self.media_root, 'images_private'))
        with open(os.path.join(self.media_root, 'images_private', 'x.txt'), 'wb') as f:
            f.write(b'x')
        with self.assertRaises(Http404):
            safe_media_path('images', '../images_private/x.txt')

    def test_rejects_symlink_escaping_subdir(self):
        os.symlink(
            os.path.join(self.media_root, 'secret.txt'),
            os.path.join(self.media_root, 'images', 'link.txt'),
        )
        with self.assertRaises(Http404):
            safe_media_path('images', 'link.txt')

    def test_rejects_missing_file(self):
        with self.assertRaises(Http404):
            safe_media_path('images', 'missing.txt')


class MkrFileViewTests(MediaFileTestMixin, TestCase):
    def test_get_image(self):
        response = self.client.get(reverse('get_image', args=['file.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'images')

    def test_get_logo(self):
        response = self.client.get(reverse('get_logo', args=['file.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'logo')

    def test_missing_files_return_404(self):
        self.assertEqual(self.client.get(reverse('get_image', args=['missing.txt'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('get_logo', args=['missing.txt'])).status_code, 404)

    def test_download_for_teacher(self):
        user = get_user_model().objects.create_user(username='t', password='x', is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse('download', args=['file.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), b'downloads')
        self.assertEqual(self.client.get(reverse('download', args=['missing.txt'])).status_code, 404)
