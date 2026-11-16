from django.contrib import admin

from .models import Club, ClubChoice, ClubSetting, Student


@admin.register(ClubSetting)
class ClubSettingAdmin(admin.ModelAdmin):
    list_display = ['title', 'voting_open', 'show_assignment']


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'max_size', 'order']
    ordering = ['order', 'name']


class ClubChoiceInline(admin.StackedInline):
    model = ClubChoice
    extra = 0
    readonly_fields = ['submitted_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'group', 'token', 'assigned']
    list_filter = ['group', 'assigned']
    search_fields = ['last_name', 'first_name', 'token']
    readonly_fields = ['token', 'created_at']
    inlines = [ClubChoiceInline]


@admin.register(ClubChoice)
class ClubChoiceAdmin(admin.ModelAdmin):
    list_display = ['student', 'choice1', 'choice2', 'choice3', 'submitted_at']
    list_filter = ['choice1']
    search_fields = ['student__last_name', 'student__first_name']
    readonly_fields = ['submitted_at']
