from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
# from django_cryptography.fields import encrypt


# class Config(models.Model):
#     NAME_CHOICES = [
#         ('E-Mail', 'Ziel-E-Mail für Schadenmeldungen'),
#         ('noreply-mail', 'noreply-E-Mail zum Versand der Schadenmeldung'),
#         ('info-frontpage', 'info-frontpage'),
#     ]
#     name = models.CharField(max_length=50, choices=NAME_CHOICES)
#     setting = models.CharField(max_length=30, blank=True)
#     text = RichTextField(blank=True)

#     def __str__(self):
#         return self.setting


class Setting(models.Model):
    name = models.CharField(max_length=50, blank=True)
    institution = models.CharField(max_length=50, blank=True)
    logo = models.FileField(blank=True, upload_to='logo/')
    # access_token = models.CharField(max_length=500, blank=True)
    student_access_token = models.CharField(max_length=500, blank=True)
    email_to = models.CharField(max_length=50, blank=True)
    noreply_mail = models.CharField(max_length=50, blank=True)
    dsb_link = models.URLField(blank=True)
    mkr_link = models.URLField(blank=True)
    # email_host = models.CharField(max_length=50, blank=True)
    # email_use_tls = models.BooleanField(default=True)
    # email_port = models.IntegerField(default=587)
    # email_host_user = models.CharField(max_length=50, blank=True)
    # email_host_password_enc = models.CharField(max_length=50, blank=True)
    info_frontpage = CKEditor5Field(blank=True, config_name='extends')
