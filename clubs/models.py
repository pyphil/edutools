from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class ClubSetting(models.Model):
    title = models.CharField(max_length=300)

    def __str__(self):
        return self.title


class Club(models.Model):
    """Represents an available Arbeitsgemeinschaft (club)."""
    name = models.CharField(max_length=200)
    max_size = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order", "name"]


class StudentUpload(models.Model):
    """CSV upload by a teacher containing student list and optional extra columns.
    The raw file is kept for auditing; parsing/matching is handled elsewhere.
    """
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    csv_file = models.FileField(upload_to='uploads/clubs/')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Student upload {self.uploaded_at:%Y-%m-%d %H:%M}"


class ClubChoice(models.Model):
    """Stores a student's club choices (three preferences) and an optional assignment."""
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    choice1 = models.ForeignKey(Club, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    choice2 = models.ForeignKey(Club, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    choice3 = models.ForeignKey(Club, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    assigned = models.ForeignKey(Club, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_students')

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a name by stripping whitespace and lowercasing for comparison."""
        if name is None:
            return ''
        return name.strip().lower()

    def normalized_full_name(self) -> str:
        return f"{self.normalize_name(self.first_name)} {self.normalize_name(self.last_name)}"

    def apply_first_choice_if_available(self):
        """Set assigned to first choice if not already assigned."""
        if not self.assigned and self.choice1:
            self.assigned = self.choice1
            self.save()
