from django.db import models
from buchungstool.models import Room


class Device(models.Model):
    def get_next_number():
        """
        Returns the next integer value in the dataset.
        """
        devices = Device.objects.all()
        if devices.count() == 0:
            return 1
        else:
            return devices.aggregate(models.Max('position'))['position__max'] + 1
    device = models.CharField(max_length=30)
    dbname = models.CharField(max_length=10, blank=True, null=True)
    position = models.PositiveIntegerField(default=get_next_number)

    def __str__(self):
        return self.device

    class Meta:
        ordering = ['position']


class Status(models.Model):
    status = models.CharField(max_length=20)
    color = models.CharField(max_length=20)

    def __str__(self):
        return self.status

    class Meta:
        verbose_name_plural = "Status"


class DevicelistEntry(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # device = models.CharField(max_length=10)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    datum = models.DateField()
    stunde = models.IntegerField()
    beschreibung = models.CharField(max_length=300)
    krzl = models.CharField(max_length=10)
    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING, default=1)
    behoben = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = "DevicelistEntries"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        age = today - self.datum
        age = str(age).split('d')[0].strip()
        return age
