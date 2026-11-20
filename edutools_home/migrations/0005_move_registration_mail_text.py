from django.db import migrations

from edutools_home.models import DEFAULT_REGISTRATION_MAIL_TEXT

SETTINGS_NAME = 'settings'
OLD_CONFIG_NAME = 'accounts_mail_text'


def move_registration_mail_text(apps, schema_editor):
    """
    Move the registration mail text from the WLANCodesWebApp Config entry
    'accounts_mail_text' to the eduTools settings. Without an old text the
    default text is used, so a fresh database starts with a working mail text.
    """
    EdutoolsSetting = apps.get_model('edutools_home', 'EdutoolsSetting')
    Config = apps.get_model('WLANCodesWebApp', 'Config')

    old_configs = Config.objects.filter(name=OLD_CONFIG_NAME)
    old_text = next((c.text.strip() for c in old_configs if c.text and c.text.strip()), '')

    settings_obj, created = EdutoolsSetting.objects.get_or_create(name=SETTINGS_NAME)
    settings_obj.registration_mail_text = old_text or DEFAULT_REGISTRATION_MAIL_TEXT
    settings_obj.save()

    old_configs.delete()


def restore_registration_mail_text(apps, schema_editor):
    EdutoolsSetting = apps.get_model('edutools_home', 'EdutoolsSetting')
    Config = apps.get_model('WLANCodesWebApp', 'Config')

    settings_obj = EdutoolsSetting.objects.filter(name=SETTINGS_NAME).first()
    if settings_obj and settings_obj.registration_mail_text:
        Config.objects.update_or_create(
            name=OLD_CONFIG_NAME,
            defaults={'text': settings_obj.registration_mail_text},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('edutools_home', '0004_edutoolssetting_registration_mail_text'),
        ('WLANCodesWebApp', '0017_allowedemail_alter_config_name'),
    ]

    operations = [
        migrations.RunPython(move_registration_mail_text, restore_registration_mail_text),
    ]
