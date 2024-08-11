from django.forms import ModelForm
from django import forms
from .models import Kompetenzkarte
from django.utils.safestring import mark_safe


class KompetenzkarteForm(ModelForm):
    class Meta:
        model = Kompetenzkarte
        fields = (
            'kategorie',
            'fach',
            'jgst',
            'vorhaben',
            'info',
            'medienkompetenz',
            'vorwissen_sus',
            'technik',
            'medienkenntnisse_lul',
            'alle_teil',
            'pflicht_empf',
            'durchf_planung',
            'download',
        )
        labels = {
            'kategorie': mark_safe('<strong>Kategorie im Medienkompetenzrahmen</strong>'),
            'fach': mark_safe('<strong>Fach</strong>'),
            'jgst': mark_safe('<strong>Jahrgangsstufe</strong>'),
            'vorhaben': mark_safe('<strong>Unterrichtsvorhaben (Titel)</strong>'),
            'info': mark_safe('<strong>Detaillierte Informationen befinden sich hier (z.B. schulinternes Curriculum/Fachschaftsordner etc.)</strong>'),
            'medienkompetenz': mark_safe('<strong>Medienkompetenz</strong>'),
            'vorwissen_sus': mark_safe('<strong>Benötigtes Vorwissen der Schüler:innen</strong>'),
            'technik': mark_safe('<strong>Benötigte Technik/Software</strong>'),
            'medienkenntnisse_lul': mark_safe('<strong>Vorausgesetzte Medienkenntnisse der Lehrer:innen</strong>'),
            'alle_teil': mark_safe('<strong>Das Vorhaben ...</strong>'),
            'pflicht_empf': mark_safe('<strong>Das Vorhaben ...</strong>'),
            'durchf_planung': mark_safe('<strong>Das Vorhaben ...</strong>'),
            'download': mark_safe('<strong>Dateianhang für internen Bereich (Material, Konzept)</strong>')
        }
        widgets = {
            'kategorie': forms.Select(attrs={'class': 'form-select'}),
            'fach': forms.Select(attrs={'class': 'form-select'}),
            'jgst': forms.Select(attrs={'class': 'form-select'}),
            'vorhaben': forms.TextInput(attrs={'class': 'form-control'}),
            'info': forms.TextInput(attrs={'class': 'form-control'}),
            'medienkompetenz': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
            'vorwissen_sus': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'technik': forms.TextInput(attrs={'class': 'form-control'}),
            'medienkenntnisse_lul': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            # 'alle_teil': forms.Select(),
            'alle_teil': forms.Select(attrs={'class': 'form-select form-select-sm', 'style': 'width: 200px;'}),
            # 'pflicht_empf': forms.RadioSelect(),
            'pflicht_empf': forms.Select(attrs={'class': 'form-select form-select-sm', 'style': 'width: 200px;'}),
            # 'durchf_planung': forms.RadioSelect(),
            'durchf_planung': forms.Select(attrs={'class': 'form-select form-select-sm', 'style': 'width: 200px;'}),
            'download': forms.ClearableFileInput({'class': 'form-control'}),
        }
