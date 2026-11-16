from django.core.validators import MinValueValidator
from django.db import models

from .tokens import format_token, generate_unique_token


class ClubSetting(models.Model):
    """Global settings of the club election (only one row is used)."""
    title = models.CharField('Titel', max_length=300, default='AG-Wahl')
    intro_text = models.TextField(
        'Hinweise für Schüler:innen', blank=True,
        help_text='Wird auf der Wahlseite über dem Formular angezeigt.',
    )
    voting_open = models.BooleanField(
        'Wahl geöffnet', default=False,
        help_text='Nur bei geöffneter Wahl können Schüler:innen ihre Wünsche abgeben oder ändern.',
    )
    show_assignment = models.BooleanField(
        'Zuordnung für Schüler:innen sichtbar', default=False,
        help_text='Schüler:innen sehen nach Eingabe ihres Codes, welcher AG sie zugeordnet wurden.',
    )

    def __str__(self):
        return self.title

    @classmethod
    def get(cls):
        obj = cls.objects.order_by('pk').first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class Club(models.Model):
    """An Arbeitsgemeinschaft (club) students can choose."""
    name = models.CharField('Name', max_length=200)
    leader = models.CharField('Leitung', max_length=200, blank=True)
    description = models.TextField('Beschreibung', blank=True)
    max_size = models.PositiveIntegerField(
        'max. Teilnehmende', blank=True, null=True, validators=[MinValueValidator(1)],
    )
    order = models.PositiveIntegerField('Reihenfolge', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'AG'
        verbose_name_plural = 'AGs'

    def __str__(self):
        return self.name


class Student(models.Model):
    """An imported student. The token is the personal Wahlcode."""
    last_name = models.CharField('Nachname', max_length=200)
    first_name = models.CharField('Vorname', max_length=200)
    group = models.CharField('Klasse', max_length=20, blank=True)
    token = models.CharField('Wahlcode', max_length=16, unique=True, editable=False)
    assigned = models.ForeignKey(
        Club, verbose_name='zugeordnete AG', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_students',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['group', 'last_name', 'first_name']
        verbose_name = 'Schüler:in'
        verbose_name_plural = 'Schüler:innen'

    def __str__(self):
        return f'{self.last_name}, {self.first_name} ({self.group})'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_unique_token(Student)
        super().save(*args, **kwargs)

    def regenerate_token(self):
        self.token = generate_unique_token(Student)
        self.save(update_fields=['token'])

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def display_token(self):
        return format_token(self.token)

    def get_choice(self):
        try:
            return self.choice
        except ClubChoice.DoesNotExist:
            return None

    def wish_ids(self):
        choice = self.get_choice()
        if choice is None:
            return []
        return [choice.choice1_id, choice.choice2_id, choice.choice3_id]

    def assigned_rank(self):
        """1, 2 or 3 if the assigned club was one of the wishes, else None."""
        if not self.assigned_id:
            return None
        ids = self.wish_ids()
        if self.assigned_id in ids:
            return ids.index(self.assigned_id) + 1
        return None


class ClubChoice(models.Model):
    """The wishes a student submitted with their Wahlcode."""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='choice')
    choice1 = models.ForeignKey(
        Club, verbose_name='1. Wunsch', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='first_choices',
    )
    choice2 = models.ForeignKey(
        Club, verbose_name='2. Wunsch', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='second_choices',
    )
    choice3 = models.ForeignKey(
        Club, verbose_name='3. Wunsch', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='third_choices',
    )
    submitted_at = models.DateTimeField('abgegeben am', auto_now=True)

    class Meta:
        verbose_name = 'Wahl'
        verbose_name_plural = 'Wahlen'

    def __str__(self):
        return f'Wahl von {self.student}'

    def wishes(self):
        return [c for c in (self.choice1, self.choice2, self.choice3) if c is not None]
