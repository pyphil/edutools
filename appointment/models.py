from django.db import models


class Appointment(models.Model):
    student_name = models.CharField(max_length=200, blank=True)
    parents_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=200)
    email_2 = models.EmailField(max_length=200)
    date = models.DateField()
    time = models.TimeField()

    class Meta:
        ordering = ['time']
