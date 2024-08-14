from django.db import models


class Appointment(models.Model):
    student_name = models.CharField(max_length=200, blank=True)
    booked = models.BooleanField()
    date = models.DateField()
    time = models.TimeField()
