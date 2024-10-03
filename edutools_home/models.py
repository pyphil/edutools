from django.db import models
# from django_ckeditor_5.fields import CKEditor5Field


class EdutoolsSetting(models.Model):
    name = models.CharField(max_length=10, blank=True)
    login_hint = models.TextField(blank=True)
    legal_notice = models.URLField(blank=True)
    privacy_policy = models.URLField(blank=True)

    def __str__(self):
        return self.name
