from django.contrib import admin
from .models import RegistrationID, UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    # fields to display in the listing
    list_display = (
        "abbr",
        "email",
        "user",
    )

    # enable results filtering
    list_filter = (
        "abbr",
        "user",
    )

    # number of items per page
    # list_per_page = 25
    list_max_show_all = 2000

    # Default results ordering
    ordering = ["-abbr"]


admin.site.register(RegistrationID)
admin.site.register(UserProfile, UserProfileAdmin)
