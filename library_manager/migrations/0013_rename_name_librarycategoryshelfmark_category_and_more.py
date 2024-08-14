# Generated by Django 5.0.3 on 2024-07-01 20:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0012_remove_inventoryitem_existing'),
    ]

    operations = [
        migrations.RenameField(
            model_name='librarycategoryshelfmark',
            old_name='name',
            new_name='category',
        ),
        migrations.AddField(
            model_name='librarycategoryshelfmark',
            name='shelfmark',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='category_shelfmark',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='library_manager.librarycategoryshelfmark'),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='library_manager.librarylocation'),
        ),
    ]