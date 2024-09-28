from django.contrib import admin
from .models import Activity, ActivityBlock, BookedActivity


admin.site.register(Activity)
admin.site.register(ActivityBlock)
admin.site.register(BookedActivity)
