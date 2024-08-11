from django.db import models
from django.utils import timezone


class LibraryCategoryShelfmark(models.Model):
    category = models.CharField(max_length=50, unique=True)
    shelfmark = models.CharField(max_length=50, unique=True)

    def __str__(self):
        if not self.category:
            self.category = ""
        return self.category + '/' + self.shelfmark

    class Meta:
        ordering = ['category']

    @property
    def items_in_category(self):
        items = InventoryItem.objects.filter(category_shelfmark=self)
        return len(items)


class LibraryLocation(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        if not self.name:
            self.name = ""
        return self.name


class LibraryStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        if not self.name:
            self.name = ""
        return self.name


class InventoryItem(models.Model):
    author = models.CharField(max_length=120)
    title = models.CharField(max_length=120)
    category_shelfmark = models.ForeignKey(LibraryCategoryShelfmark, on_delete=models.PROTECT)
    inventory_number = models.IntegerField(blank=True, unique=True)
    location = models.ForeignKey(LibraryLocation, on_delete=models.PROTECT)
    status = models.ForeignKey(LibraryStatus, on_delete=models.PROTECT)
    notes = models.TextField(max_length=10000, blank=True, null=True)

    @property
    def next_inventory_number(self):
        obj = InventoryItem.objects.all()
        if obj.count() == 0:
            return 1
        else:
            return obj.aggregate(models.Max('inventory_number'))['inventory_number__max'] + 1

    @property
    def borrowed(self):
        try:
            borrowed = LibraryBorrowedItem.objects.get(book=self)
        except LibraryBorrowedItem.DoesNotExist:
            borrowed = None
        return borrowed


class LibraryBorrowedItem(models.Model):
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school_class = models.CharField(max_length=100)
    book = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, blank=True)
    borrowing_date = models.DateField(blank=True)
    return_date = models.DateField(blank=True, null=True)

    @property
    def return_overdue(self):
        if self.return_date < timezone.now().date():
            diff = timezone.now().date() - self.return_date
            return diff.days
        else:
            return None

    class Meta:
        ordering = ['return_date']
