from django.db import models


class Appointment(models.Model):
    student_name = models.CharField(max_length=200, blank=True)
    primary_school = models.CharField(max_length=300, blank=True)
    parents_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=200, blank=True)
    email_2 = models.EmailField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    date = models.DateField()
    time = models.TimeField()

    class Meta:
        ordering = ['time']


class AppointmentMail(models.Model):
    mail_text = models.TextField(blank=True, null=True)
