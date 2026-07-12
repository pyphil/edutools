from django import forms
from .models import Key, DsbName
from upload.models import UploadKey


class KeyForm(forms.ModelForm):
    class Meta:
        model = Key
        fields = ["key"]
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control", "placeholder": "Zugangsschlüssel"}),
        }
        labels = {
            "key": "Zugangsschlüssel",
        }


class UploadKeyForm(forms.ModelForm):
    class Meta:
        model = UploadKey
        fields = ["key"]
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control", "placeholder": "Upload-Schlüssel"}),
        }
        labels = {
            "key": "Upload-Schlüssel",
        }


class DsbNameForm(forms.ModelForm):
    class Meta:
        model = DsbName
        fields = ["dsb1", "dsb2"]
        widgets = {
            "dsb1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bezeichnung für DSB1"}),
            "dsb2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bezeichnung für DSB2"}),
        }
        labels = {
            "dsb1": "DSB1 Name",
            "dsb2": "DSB2 Name",
        }
