# Generated by Django 4.2.16 on 2025-01-23 07:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_alter_activity_options_alter_bookedactivity_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bookedactivity',
            options={'ordering': ['student_name'], 'verbose_name_plural': 'Booked Activities'},
        ),
    ]
