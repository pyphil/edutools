from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class Booking(models.Model):
    room = models.CharField(max_length=10)
    krzl = models.CharField(max_length=3)
    lerngruppe = models.CharField(max_length=30)
    datum = models.DateField()
    stunde = models.IntegerField()
    series_id = models.CharField(max_length=32, blank=True)
    iPad_01 = models.CharField(max_length=120, blank=True)
    iPad_02 = models.CharField(max_length=120, blank=True)
    iPad_03 = models.CharField(max_length=120, blank=True)
    iPad_04 = models.CharField(max_length=120, blank=True)
    iPad_05 = models.CharField(max_length=120, blank=True)
    iPad_06 = models.CharField(max_length=120, blank=True)
    iPad_07 = models.CharField(max_length=120, blank=True)
    iPad_08 = models.CharField(max_length=120, blank=True)
    iPad_09 = models.CharField(max_length=120, blank=True)
    iPad_10 = models.CharField(max_length=120, blank=True)
    iPad_11 = models.CharField(max_length=120, blank=True)
    iPad_12 = models.CharField(max_length=120, blank=True)
    iPad_13 = models.CharField(max_length=120, blank=True)
    iPad_14 = models.CharField(max_length=120, blank=True)
    iPad_15 = models.CharField(max_length=120, blank=True)
    iPad_16 = models.CharField(max_length=120, blank=True)
    iPad_17 = models.CharField(max_length=120, blank=True)
    iPad_18 = models.CharField(max_length=120, blank=True)
    iPad_19 = models.CharField(max_length=120, blank=True)
    iPad_20 = models.CharField(max_length=120, blank=True)
    iPad_21 = models.CharField(max_length=120, blank=True)
    iPad_22 = models.CharField(max_length=120, blank=True)
    iPad_23 = models.CharField(max_length=120, blank=True)
    iPad_24 = models.CharField(max_length=120, blank=True)
    iPad_25 = models.CharField(max_length=120, blank=True)
    iPad_26 = models.CharField(max_length=120, blank=True)
    iPad_27 = models.CharField(max_length=120, blank=True)
    iPad_28 = models.CharField(max_length=120, blank=True)
    iPad_29 = models.CharField(max_length=120, blank=True)
    iPad_30 = models.CharField(max_length=120, blank=True)
    pen_01 = models.CharField(max_length=2, blank=True)
    pen_02 = models.CharField(max_length=2, blank=True)
    pen_03 = models.CharField(max_length=2, blank=True)
    pen_04 = models.CharField(max_length=2, blank=True)
    pen_05 = models.CharField(max_length=2, blank=True)
    pen_06 = models.CharField(max_length=2, blank=True)
    pen_07 = models.CharField(max_length=2, blank=True)
    pen_08 = models.CharField(max_length=2, blank=True)
    pen_09 = models.CharField(max_length=2, blank=True)
    pen_10 = models.CharField(max_length=2, blank=True)
    pen_11 = models.CharField(max_length=2, blank=True)
    pen_12 = models.CharField(max_length=2, blank=True)
    pen_13 = models.CharField(max_length=2, blank=True)
    pen_14 = models.CharField(max_length=2, blank=True)
    pen_15 = models.CharField(max_length=2, blank=True)
    pen_16 = models.CharField(max_length=2, blank=True)
    pen_17 = models.CharField(max_length=2, blank=True)
    pen_18 = models.CharField(max_length=2, blank=True)
    pen_19 = models.CharField(max_length=2, blank=True)
    pen_20 = models.CharField(max_length=2, blank=True)
    pen_21 = models.CharField(max_length=2, blank=True)
    pen_22 = models.CharField(max_length=2, blank=True)
    pen_23 = models.CharField(max_length=2, blank=True)
    pen_24 = models.CharField(max_length=2, blank=True)
    pen_25 = models.CharField(max_length=2, blank=True)
    pen_26 = models.CharField(max_length=2, blank=True)
    pen_27 = models.CharField(max_length=2, blank=True)
    pen_28 = models.CharField(max_length=2, blank=True)
    pen_29 = models.CharField(max_length=2, blank=True)
    pen_30 = models.CharField(max_length=2, blank=True)


class Category(models.Model):
    def get_next_number():
        """
        Returns the next integer value in the dataset.
        """
        categories = Category.objects.all()
        if categories.count() == 0:
            return 1
        else:
            return categories.aggregate(models.Max('position'))['position__max'] + 1

    name = models.CharField(max_length=100)
    position = models.PositiveSmallIntegerField(default=get_next_number)
    color = models.CharField(max_length=7, default='#ebebeb')
    column_break = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['position']


class Room(models.Model):
    def get_next_number():
        """
        Returns the next integer value in the dataset.
        """
        rooms = Room.objects.all()
        if rooms.count() == 0:
            return 1
        else:
            return rooms.aggregate(models.Max('position'))['position__max'] + 1

    short_name = models.CharField(max_length=10)
    room = models.CharField(max_length=50)
    DEVICE_COUNT_CHOICES = []
    for i in range(1, 31):
        DEVICE_COUNT_CHOICES.append((str(i), str(i)))
    device_count = models.CharField(max_length=5, choices=DEVICE_COUNT_CHOICES, blank=True)
    description = models.CharField(max_length=100)
    card = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, blank=True, null=True)
    alert = CKEditor5Field(blank=True, config_name='extends')
    position = models.PositiveIntegerField(default=get_next_number)
    is_first_of_category = models.BooleanField(default=False)
    is_last_of_category = models.BooleanField(default=False)

    def __str__(self):
        return f"{ self.room } - { self.description }"

    class Meta:
        ordering = ['category', 'position']


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = CKEditor5Field(blank=True, config_name='extends')

    def __str__(self):
        return self.question
