# Generated by Django 5.0.3 on 2024-07-01 19:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0011_rename_librarycategory_librarycategoryshelfmark_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventoryitem',
            name='existing',
        ),
    ]