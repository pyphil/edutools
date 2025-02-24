from django.db import models


class ActivityBlock(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Activity(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Activities'


class BookedActivity(models.Model):
    block = models.ForeignKey(ActivityBlock, on_delete=models.PROTECT)
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT)
    student_name = models.CharField(max_length=200)
    parents_name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'Booked Activities'
        ordering = ['student_name']
