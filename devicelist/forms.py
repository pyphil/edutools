from django.forms import ModelForm
from django import forms
from .models import DevicelistEntry


class DevicelistEntryForm(ModelForm):
    class Meta:
        model = DevicelistEntry
        fields = (
            'room',
            'device',
            'datum',
            'stunde',
            'beschreibung',
            'krzl'
        )
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'datum': forms.TextInput(attrs={'type': 'date', 'class': 'form-control', 'style': "height: 38px;"}),
            'stunde': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 11}),
            'beschreibung': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'krzl': forms.TextInput(attrs={'class': 'form-control'})
        }


class DevicelistEntryFormLoggedIn(ModelForm):
    class Meta:
        model = DevicelistEntry
        fields = (
            'room',
            'device',
            'datum',
            'stunde',
            'beschreibung',
            'krzl',
            'status',
            'behoben'
        )
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'datum': forms.TextInput(attrs={'type': 'date', 'class': 'form-control', 'style': "height: 38px;"}),
            'stunde': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 11}),
            'beschreibung': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'krzl': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'behoben': forms.TextInput(attrs={'class': 'form-control'}),
        }
