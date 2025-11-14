from django import forms
from .models import ActivityBlock, Activity, ActivitySetting


class ActivitySettingForm(forms.ModelForm):
    class Meta:
        model = ActivitySetting
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ActivityBlockForm(forms.ModelForm):
    class Meta:
        model = ActivityBlock
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
