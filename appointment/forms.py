from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'student_name',
        ]
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
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
