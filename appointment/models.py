from django.db import models


class Appointment(models.Model):
    student_name = models.CharField(max_length=200, blank=True)
    primary_school = models.CharField(max_length=300, blank=True)
    parents_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    date = models.DateField()
    time = models.TimeField()
    visible = models.BooleanField(default=True)

    # personal data fields that are filled in when booking and cleared when emptying a slot
    PERSONAL_FIELDS = ('student_name', 'primary_school', 'parents_name', 'email', 'phone')

    class Meta:
        ordering = ['time']

    @property
    def is_booked(self):
        return self.student_name != ""


class AppointmentMail(models.Model):
    mail_text = models.TextField(blank=True, null=True)
    mail_text_reminder = models.TextField(blank=True, null=True)


class AppointmentSetting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    show_empty_days = models.BooleanField(default=True)
    privacy_notice = models.TextField(blank=True, default="")
