from django.forms import ModelForm
from django import forms
from .models import QRCodeModel


class QRCodeForm(ModelForm):
    class Meta:
        model = QRCodeModel
        fields = (
            'url',
        )
        labels = {
            'url': 'URL (Internetadresse mit https://...)',
        }
        widgets = {
            'url': forms.TextInput(attrs={'class': 'form-control'}),
        }
