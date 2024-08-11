# Generated by Django 4.0.2 on 2022-09-04 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('E-Mail', 'Ziel-E-Mail für Schadenmeldungen'), ('noreply-mail', 'noreply-E-Mail zum Versand der Schadenmeldung')], max_length=50)),
                ('setting', models.CharField(max_length=100)),
            ],
        ),
    ]
