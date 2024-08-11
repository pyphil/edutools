from django.contrib import admin
from .models import Kompetenzkarte, Fach


class KompetenzkarteCustomAdmin(admin.ModelAdmin):
    list_display = (
        'kategorie', 'fach', 'jgst', 'vorhaben', 'info', 'medienkompetenz',
        'technik', 'alle_teil', 'pflicht_empf', 'durchf_planung', 'user',
        )
    list_filter = (
        'kategorie', 'fach', 'jgst', 'alle_teil', 'pflicht_empf', 'durchf_planung', 'user',
        )
    readonly_fields = ('created', 'changed',)


class FachCustomAdmin(admin.ModelAdmin):
    list_display = ('id', 'fach')
    ordering = ['fach']


admin.site.register(Kompetenzkarte, KompetenzkarteCustomAdmin)
admin.site.register(Fach, FachCustomAdmin)
