# Generated by Django 5.0.3 on 2024-03-27 17:52

import django_ckeditor_5.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('buchungstool', '0036_alter_faq_answer_alter_room_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faq',
            name='answer',
            field=django_ckeditor_5.fields.CKEditor5Field(blank=True),
        ),
    ]
