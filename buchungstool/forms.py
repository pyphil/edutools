from django.forms import ModelForm
from django import forms
from .models import Booking, Room, FAQ


class BookingFormIpad(ModelForm):
    class Meta:
        model = Booking
        fields = [
            'iPad_01', 'iPad_02', 'iPad_03', 'iPad_04', 'iPad_05',
            'iPad_06', 'iPad_07', 'iPad_08', 'iPad_09', 'iPad_10',
            'iPad_11', 'iPad_12', 'iPad_13', 'iPad_14', 'iPad_15', 'iPad_16',
            'iPad_12', 'iPad_13', 'iPad_14', 'iPad_15', 'iPad_16', 'iPad_17',
            'iPad_18', 'iPad_19', 'iPad_20', 'iPad_21', 'iPad_22', 'iPad_23',
            'iPad_24', 'iPad_25', 'iPad_26', 'iPad_27', 'iPad_28', 'iPad_29', 'iPad_30',
            'pen_01', 'pen_02', 'pen_03', 'pen_04', 'pen_05',
            'pen_06', 'pen_07', 'pen_08', 'pen_09', 'pen_10',
            'pen_11', 'pen_12', 'pen_13', 'pen_14', 'pen_15', 'pen_16',
            'pen_12', 'pen_13', 'pen_14', 'pen_15', 'pen_16', 'pen_17',
            'pen_18', 'pen_19', 'pen_20', 'pen_21', 'pen_22', 'pen_23',
            'pen_24', 'pen_25', 'pen_26', 'pen_27', 'pen_28', 'pen_29', 'pen_30',
        ]
        widgets = {}
        for field in fields:
            widgets[field] = forms.TextInput(attrs={'class': 'form-control'})


class RoomAlertForm(ModelForm):
    class Meta:
        model = Room
        fields = (
            'alert',
        )
        labels = {
            'alert': 'Du bist eingeloggt und kannst einen Hinweis zu diesem Raum/Standort erstellen oder bearbeiten'
        }


class FAQForm(ModelForm):
    class Meta:
        model = FAQ
        exclude = {}
        labels = {
            'question': 'Frage',
            'answer': 'Antwort',
        }
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
        }
