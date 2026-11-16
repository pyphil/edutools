import secrets

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def _token(Student):
    while True:
        token = ''.join(secrets.choice(ALPHABET) for _ in range(8))
        if not Student.objects.filter(token=token).exists():
            return token


def move_names_to_students(apps, schema_editor):
    """Each old ClubChoice row (name + wishes) becomes a Student with a Wahlcode.
    Rows without any wish (placeholders of the old CSV import) keep only the Student.
    """
    ClubChoice = apps.get_model('clubs', 'ClubChoice')
    Student = apps.get_model('clubs', 'Student')
    for choice in ClubChoice.objects.all():
        student = Student.objects.create(
            first_name=choice.first_name,
            last_name=choice.last_name,
            group='',
            token=_token(Student),
            assigned_id=choice.assigned_id,
        )
        if choice.choice1_id or choice.choice2_id or choice.choice3_id:
            choice.student = student
            choice.save(update_fields=['student'])
        else:
            choice.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0001_initial'),
    ]

    operations = [
        # free the related_name "assigned_students" for Student.assigned
        migrations.AlterField(
            model_name='clubchoice',
            name='assigned',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='clubs.club'),
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_name', models.CharField(max_length=200, verbose_name='Nachname')),
                ('first_name', models.CharField(max_length=200, verbose_name='Vorname')),
                ('group', models.CharField(blank=True, max_length=20, verbose_name='Klasse')),
                ('token', models.CharField(editable=False, max_length=16, unique=True, verbose_name='Wahlcode')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_students', to='clubs.club', verbose_name='zugeordnete AG')),
            ],
            options={
                'verbose_name': 'Schüler:in',
                'verbose_name_plural': 'Schüler:innen',
                'ordering': ['group', 'last_name', 'first_name'],
            },
        ),
        migrations.AddField(
            model_name='clubchoice',
            name='student',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='choice', to='clubs.student'),
        ),
        migrations.RunPython(move_names_to_students, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name='clubchoice',
            options={'verbose_name': 'Wahl', 'verbose_name_plural': 'Wahlen'},
        ),
        migrations.RemoveField(model_name='clubchoice', name='first_name'),
        migrations.RemoveField(model_name='clubchoice', name='last_name'),
        migrations.RemoveField(model_name='clubchoice', name='assigned'),
        migrations.AlterField(
            model_name='clubchoice',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='choice', to='clubs.student'),
        ),
        migrations.AlterField(
            model_name='clubchoice',
            name='submitted_at',
            field=models.DateTimeField(auto_now=True, verbose_name='abgegeben am'),
        ),
        migrations.AlterField(
            model_name='clubchoice',
            name='choice1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_choices', to='clubs.club', verbose_name='1. Wunsch'),
        ),
        migrations.AlterField(
            model_name='clubchoice',
            name='choice2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='second_choices', to='clubs.club', verbose_name='2. Wunsch'),
        ),
        migrations.AlterField(
            model_name='clubchoice',
            name='choice3',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='third_choices', to='clubs.club', verbose_name='3. Wunsch'),
        ),
        # The raw CSV upload is no longer stored (data protection); parsing happens in memory.
        migrations.DeleteModel(name='StudentUpload'),
        migrations.AlterModelOptions(
            name='club',
            options={'ordering': ['order', 'name'], 'verbose_name': 'AG', 'verbose_name_plural': 'AGs'},
        ),
        migrations.AddField(
            model_name='club',
            name='leader',
            field=models.CharField(blank=True, max_length=200, verbose_name='Leitung'),
        ),
        migrations.AddField(
            model_name='club',
            name='description',
            field=models.TextField(blank=True, verbose_name='Beschreibung'),
        ),
        migrations.AlterField(
            model_name='club',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='club',
            name='max_size',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='max. Teilnehmende'),
        ),
        migrations.AlterField(
            model_name='club',
            name='order',
            field=models.PositiveIntegerField(default=0, verbose_name='Reihenfolge'),
        ),
        migrations.AlterField(
            model_name='clubsetting',
            name='title',
            field=models.CharField(default='AG-Wahl', max_length=300, verbose_name='Titel'),
        ),
        migrations.AddField(
            model_name='clubsetting',
            name='intro_text',
            field=models.TextField(blank=True, help_text='Wird auf der Wahlseite über dem Formular angezeigt.', verbose_name='Hinweise für Schüler:innen'),
        ),
        migrations.AddField(
            model_name='clubsetting',
            name='voting_open',
            field=models.BooleanField(default=False, help_text='Nur bei geöffneter Wahl können Schüler:innen ihre Wünsche abgeben oder ändern.', verbose_name='Wahl geöffnet'),
        ),
        migrations.AddField(
            model_name='clubsetting',
            name='show_assignment',
            field=models.BooleanField(default=False, help_text='Schüler:innen sehen nach Eingabe ihres Codes, welcher AG sie zugeordnet wurden.', verbose_name='Zuordnung für Schüler:innen sichtbar'),
        ),
    ]
