from django.db import models


class Key(models.Model):
    key = models.CharField(max_length=50)

    def __str__(self):
        return self.key


class DsbName(models.Model):
    dsb1 = models.CharField(max_length=100, blank=True, null=True)
    dsb2 = models.CharField(max_length=100, blank=True, null=True)
