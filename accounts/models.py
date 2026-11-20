from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    abbr = models.CharField(max_length=3)
    email = models.EmailField()
    user = models.OneToOneField(User, on_delete=models.PROTECT, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.abbr = self.abbr.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.abbr


class RegistrationID(models.Model):
    user_email = models.EmailField()
    uuid = models.CharField(max_length=32)
    created = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        max_age = timedelta(hours=settings.ACCOUNTS_REGISTRATION_LINK_TIMEOUT_HOURS)
        return self.created < timezone.now() - max_age

    def __str__(self):
        return self.user_email
