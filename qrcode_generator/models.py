from django.db import models
from django.contrib.auth.models import User


class QRCodeModel(models.Model):
    image = models.ImageField(upload_to='qr_codes/')
    url = models.URLField()
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
