from django.db import models


# Create your models here.
class UploadKey(models.Model):
    key = models.CharField(max_length=50)

    def __str__(self):
        return self.key


class Upload(models.Model):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to="upload", blank=True, null=True)


class UploadLaufband(models.Model):
    name = models.CharField(max_length=100)
    text_nz = models.CharField(max_length=500, blank=True, null=True)
    text_mz = models.CharField(max_length=500, blank=True, null=True)
