from django.db import models


class Activity(models.Model):
    student_name = models.CharField(max_length=200)
