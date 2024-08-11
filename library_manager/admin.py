from django.contrib import admin
from .models import LibraryCategoryShelfmark, LibraryLocation, InventoryItem, LibraryStatus, LibraryBorrowedItem


class InventoryItemCustomAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = ('id',
                    'author',
                    'title',
                    'category_shelfmark',
                    'inventory_number',
                    'status',
                    'location',
                )

    # enable results filtering
    list_filter = ('category_shelfmark',
                   'location',)

    # number of items per page
    # list_per_page = 25
    list_max_show_all = 2000

    # Default results ordering
    # ordering = ['-pub_date', 'name']


class LibraryCategoryCustomAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'shelfmark')


class LibraryBorrowedItemCustomAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'surname', 'school_class', 'book')


admin.site.register(LibraryLocation)
admin.site.register(LibraryStatus)
admin.site.register(LibraryBorrowedItem)
admin.site.register(LibraryCategoryShelfmark, LibraryCategoryCustomAdmin)
admin.site.register(InventoryItem, InventoryItemCustomAdmin)
