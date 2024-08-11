from django.contrib import admin

# Register your models here.
from .models import Booking
from .models import Room
from .models import Category
from .models import FAQ


class BookingCustomAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = ('id', 'room', 'krzl', 'lerngruppe', 'datum', 'stunde', 'series_id')

    # enable results filtering
    list_filter = ('room', 'krzl', 'lerngruppe', 'datum', 'stunde', 'series_id')

    # number of items per page
    # list_per_page = 25

    # Default results ordering
    # ordering = ['-pub_date', 'name']


class RoomCustomAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = ('short_name', 'room', 'device_count', 'description', 'card')
    list_filter = ('card', 'device_count')


admin.site.register(Booking, BookingCustomAdmin)
admin.site.register(Room, RoomCustomAdmin)
admin.site.register(Category)
admin.site.register(FAQ)
