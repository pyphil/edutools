# Generated by Django 4.2.11 on 2024-04-30 16:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library_manager', '0009_alter_librarycategory_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='library_manager.librarycategory', to_field='name'),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='library_manager.librarylocation', to_field='name'),
        ),
        migrations.AlterField(
            model_name='librarycategory',
            name='name',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='librarylocation',
            name='name',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]