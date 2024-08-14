# Generated by Django 4.0.5 on 2022-07-04 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mkr', '0006_rename_file_kompetenzkarte_download'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='alle_teil',
            field=models.CharField(choices=[('0', 'ist für alle '), ('1', 'Teilgruppe')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='durchf_planung',
            field=models.CharField(choices=[('0', 'wird durchgeführt'), ('1', 'Planung/Umsetzung')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='kompetenzkarte',
            name='pflicht_empf',
            field=models.CharField(choices=[('0', 'Pflicht'), ('1', 'Empfehlung')], max_length=1, null=True),
        ),
    ]