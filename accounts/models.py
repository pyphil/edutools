from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    abbr = models.CharField(max_length=3)
    email = models.EmailField()
    user = models.OneToOneField(User, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.abbr


class RegistrationID(models.Model):
    user_email = models.EmailField()
    uuid = models.CharField(max_length=32)

    def __str__(self):
        return self.user_email
