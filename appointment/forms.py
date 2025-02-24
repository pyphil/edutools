from django import forms
from .models import Appointment, AppointmentMail


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'student_name',
            'primary_school',
            'parents_name',
            'email',
            'email_2',
            'phone',
        ]
        labels = {
            'student_name': 'Vorname und Nachname des Kindes',
            'primary_school': 'Grundschule',
            'parents_name': 'Name(n) der/des Erziehungsberechtigten',
            'email': 'E-Mail-Adresse',
            'email_2': 'Wiederholung E-Mail-Adresse',
            'phone': 'Telefon (optional, für Rückfragen)'
        }
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parents_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_school': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_2': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enforce the field to be required conditionally if needed
        self.fields['student_name'].required = True
        self.fields['parents_name'].required = True
        self.fields['primary_school'].required = True
        self.fields['email'].required = True
        self.fields['email_2'].required = True


class MailText(forms.ModelForm):
    class Meta:
        model = AppointmentMail
        fields = [
            'mail_text',
            'mail_text_reminder',

        ]
        labels = {
            'mail_text': 'E-Mail Text Buchung',
            'mail_text_reminder': 'E-Mail Text Erinnerung',
        }
        widgets = {
            'mail_text': forms.Textarea(attrs={'class': 'form-control'}),
            'mail_text_reminder': forms.Textarea(attrs={'class': 'form-control'}),
        }
