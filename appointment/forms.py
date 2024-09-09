from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'student_name',
            'parents_name',
            'email',
            'email_2',
        ]
        labels = {
            'student_name': 'Name des Kindes',
            'parents_name': 'Name(n) der Erziehungsberechtigten',
            'email': 'E-Mail-Adresse',
            'email_2': 'Wiederholung E-Mail-Adresse',
        }
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parents_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_2': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enforce the field to be required conditionally if needed
        self.fields['student_name'].required = True


class AppointmentCreateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'date',
            'time',
        ]
        widgets = {
            'date': forms.SelectDateWidget(),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
