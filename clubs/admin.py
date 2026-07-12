from django.contrib import admin
from .models import ClubSetting, Club, ClubChoice, StudentUpload


@admin.register(ClubSetting)
class ClubSettingAdmin(admin.ModelAdmin):
    list_display = ['title']


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_size', 'order']
    ordering = ['order', 'name']


@admin.register(ClubChoice)
class ClubChoiceAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'choice1', 'choice2', 'choice3', 'assigned']
    list_filter = ['assigned', 'choice1']
    search_fields = ['first_name', 'last_name']
    readonly_fields = ['submitted_at']

    actions = ['assign_first_choice']

    def assign_first_choice(self, request, queryset):
        """Admin action to assign first choice for selected students."""
        for c in queryset:
            if c.choice1:
                c.assigned = c.choice1
                c.save()
        self.message_user(request, "First choices assigned where available.")
    assign_first_choice.short_description = "Assign first choice where available"


@admin.register(StudentUpload)
class StudentUploadAdmin(admin.ModelAdmin):
    list_display = ['uploaded_at', 'uploaded_by', 'csv_file']
    readonly_fields = ['uploaded_at']
