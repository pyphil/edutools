from django.contrib import admin
from .models import Appointment, AppointmentMail, AppointmentSetting


class AppointmentCustomAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = ('id',
                    'date',
                    'time',
                    'student_name',
                    'primary_school',
                    'parents_name',
                    'email',
                )

    # enable results filtering
    list_filter = ('date',
                   'time',)

    # number of items per page
    # list_per_page = 25
    list_max_show_all = 2000

    # Default results ordering
    ordering = ['-date', '-time']


admin.site.register(Appointment, AppointmentCustomAdmin)
admin.site.register(AppointmentMail)
admin.site.register(AppointmentSetting)
