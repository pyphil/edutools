from django.contrib import admin
from .models import DevicelistEntry
from .models import Device, Status


class DevicelistEntryCustomAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'device', 'room', 'datum', 'stunde', 'beschreibung', 'krzl', 'status', 'behoben',
    )
    list_filter = (
        'device', 'room', 'datum', 'stunde', 'beschreibung', 'krzl', 'status', 'behoben',
    )


class StatusCustomAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'color')


class DeviceCustomAdmin(admin.ModelAdmin):
    list_display = ('device', 'dbname', 'position')


admin.site.register(DevicelistEntry, DevicelistEntryCustomAdmin)
admin.site.register(Device, DeviceCustomAdmin)
admin.site.register(Status, StatusCustomAdmin)
