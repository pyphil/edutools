import code
from django.contrib import admin
from .models import Student, Code, CodeDeletion, Config, AllowedEmail


class StudentCustomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'firstname',
        'group',
        'email',
        'date',
        'code',
        )
    list_filter = (
        'name',
        'firstname',
        'group',
        'email',
        'date',
        'code',
        )


class CodeDeletionCustomAdmin(admin.ModelAdmin):
    list_display = (
        'code_to_delete',
        'name',
        'firstname',
        'group',
        )
    list_filter = (
        'code_to_delete',
        'name',
        'firstname',
        'group',
        )


class CodesCustomAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'type',
        'duration',
    )
    list_filter = (
        'code',
        'type',
        'duration',
    )


class ConfigCustomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


admin.site.register(Student, StudentCustomAdmin)
admin.site.register(Code, CodesCustomAdmin)
admin.site.register(CodeDeletion, CodeDeletionCustomAdmin)
admin.site.register(Config, ConfigCustomAdmin)
admin.site.register(AllowedEmail)