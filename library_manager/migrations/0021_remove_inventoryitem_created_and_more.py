# Generated by Django 5.0.3 on 2024-07-17 15:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0020_alter_librarycategoryshelfmark_shelfmark'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventoryitem',
            name='created',
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='last_edit',
        ),
    ]
