# Generated by Django 5.0.3 on 2024-07-21 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0021_remove_inventoryitem_created_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitem',
            name='notes',
            field=models.TextField(blank=True, max_length=10000, null=True),
        ),
    ]