# Generated by Django 4.1.1 on 2022-09-10 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WLANCodesWebApp', '0002_student_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='email',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='student',
            name='code',
            field=models.CharField(max_length=20),
        ),
    ]