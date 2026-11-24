import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import Appointment, AppointmentMail, AppointmentSetting

# Characters/patterns that never belong in a name or school name. Blocking them keeps
# links and markup out of the confirmation e-mails, which are sent from the school's address.
_FORBIDDEN_TEXT = re.compile(r"(://|www\.|@|[<>{}\[\]\\])", re.IGNORECASE)

phone_validator = RegexValidator(
    regex=r"^[0-9 +()/.\-]*$",
    message="Bitte nur Ziffern, Leerzeichen und die Zeichen + ( ) / - . verwenden.",
)


def validate_plain_text(value):
    if _FORBIDDEN_TEXT.search(value):
        raise ValidationError("Bitte keine Links, E-Mail-Adressen oder Sonderzeichen wie < > eingeben.")


class AppointmentForm(forms.ModelForm):
    email_2 = forms.EmailField(
        max_length=200,
        label="Wiederholung E-Mail-Adresse",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    # Honeypot: hidden from humans via CSS, bots tend to fill every field.
    website = forms.CharField(
        required=False,
        label="Bitte leer lassen",
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )

    class Meta:
        model = Appointment
        fields = [
            'student_name',
            'primary_school',
            'parents_name',
            'email',
            'phone',
        ]
        labels = {
            'student_name': 'Vorname und Nachname des Kindes',
            'primary_school': 'Grundschule',
            'parents_name': 'Name(n) der/des Erziehungsberechtigten',
            'email': 'E-Mail-Adresse',
            'phone': 'Telefon (optional, für Rückfragen)'
        }
        widgets = {
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parents_name': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_school': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}),
        }

    field_order = ['student_name', 'primary_school', 'parents_name', 'email', 'email_2', 'phone', 'website']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('student_name', 'parents_name', 'primary_school', 'email'):
            self.fields[name].required = True
        for name in ('student_name', 'parents_name', 'primary_school'):
            self.fields[name].validators.append(validate_plain_text)
        self.fields['phone'].validators.append(phone_validator)
        # when editing an existing booking, prefill the repetition field
        if self.instance and self.instance.email and not self.is_bound:
            self.initial.setdefault('email_2', self.instance.email)

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean_email_2(self):
        return self.cleaned_data['email_2'].strip().lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('website'):
            raise ValidationError("Die Buchung konnte nicht verarbeitet werden.")
        email, email_2 = cleaned.get('email'), cleaned.get('email_2')
        if email and email_2 and email != email_2:
            self.add_error('email_2', "Die E-Mail-Adressen stimmen nicht überein.")
        return cleaned

    def personal_data(self):
        """The cleaned personal data that is written to the appointment."""
        return {name: self.cleaned_data[name] for name in Appointment.PERSONAL_FIELDS}


class CreateAppointmentsForm(forms.Form):
    date = forms.DateField()
    start_time = forms.TimeField()
    interval = forms.IntegerField(min_value=1, max_value=480)
    number = forms.IntegerField(min_value=1, max_value=200)
    slots = forms.IntegerField(min_value=1, max_value=50)
    visible = forms.BooleanField(required=False)


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


class AppointmentSettingForm(forms.ModelForm):
    class Meta:
        model = AppointmentSetting
        fields = [
            'title',
            'description',
            'privacy_notice',
            'show_empty_days',
        ]
        labels = {
            'title': 'Titel der Terminseite',
            'description': 'Beschreibung der Terminseite',
            'privacy_notice': 'Datenschutzhinweis im Buchungsformular',
            'show_empty_days': 'Ausgebuchte Tage mit Hinweis anzeigen',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'privacy_notice': forms.Textarea(attrs={'class': 'form-control'}),
            'show_empty_days': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
