# Generated by Django 5.0.3 on 2024-07-17 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0019_alter_libraryborroweditem_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='librarycategoryshelfmark',
            name='shelfmark',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
