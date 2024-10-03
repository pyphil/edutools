from django.contrib import admin
from .models import Activity, ActivityBlock, BookedActivity


class BookedActivityCustomAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = ('id', 'block', 'activity', 'student_name', 'parents_name')

    # enable results filtering
    list_filter = ('block', 'activity',)

    # number of items per page
    list_per_page = 200

    # Default results ordering
    # ordering = ['-pub_date', 'name']


admin.site.register(Activity)
admin.site.register(ActivityBlock)
admin.site.register(BookedActivity, BookedActivityCustomAdmin)
