# Generated by Django 5.0.3 on 2024-05-11 16:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mkr', '0012_alter_kompetenzkarte_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='fach',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mkr.fach'),
        ),
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='last_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='edited_datasets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
