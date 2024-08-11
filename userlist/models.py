from django.db import models


# Create your models here.
class Userlist(models.Model):
    short_name = models.CharField(max_length=10)
    lerngruppe = models.CharField(max_length=30)
    datum = models.DateField()
    stunde = models.IntegerField()
    krzl = models.CharField(blank=True, max_length=3)
    created = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.lerngruppe + " - " + self.krzl
