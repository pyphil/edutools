# Generated by Django 4.2.11 on 2024-04-30 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0006_alter_inventoryitem_author_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='author',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]