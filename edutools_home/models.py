from django.db import models
# from django_ckeditor_5.fields import CKEditor5Field

DEFAULT_REGISTRATION_MAIL_TEXT = """Hallo,

du hast die Registrierung für eduTools angefordert. Bitte klicke auf den folgenden Link, um dein Konto anzulegen:

#LINK#

Der Link ist 48 Stunden gültig. Danach kannst du über die Registrierungsseite einen neuen Link anfordern.

Wenn du diese Registrierung nicht angefordert hast, kannst du diese E-Mail ignorieren.

Viele Grüße vom eduTools-Admin
"""


class EdutoolsSetting(models.Model):
    name = models.CharField(max_length=10, blank=True)
    login_hint = models.TextField(blank=True)
    legal_notice = models.URLField(blank=True)
    privacy_policy = models.URLField(blank=True)
    registration_mail_text = models.TextField(
        'Mailtext bei Accounterstellung',
        blank=True,
        default=DEFAULT_REGISTRATION_MAIL_TEXT,
        help_text='Text der E-Mail mit dem Registrierungslink. Der Platzhalter #LINK# '
                  'wird durch den Link ersetzt und muss enthalten sein.',
    )

    def __str__(self):
        return self.name
