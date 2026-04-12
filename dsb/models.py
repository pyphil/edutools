from django.db import models


class Key(models.Model):
    key = models.CharField(max_length=50)

    def __str__(self):
        return self.key
