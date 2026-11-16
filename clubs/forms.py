from django import forms

from .models import Club, ClubSetting, Student
from .tokens import TOKEN_LENGTH, normalize_token


class TokenForm(forms.Form):
    code = forms.CharField(
        label='Dein Wahlcode',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center font-monospace text-uppercase',
            'placeholder': 'XXXX-XXXX',
            'autocomplete': 'off',
            'autocapitalize': 'characters',
            'spellcheck': 'false',
        }),
    )

    def clean_code(self):
        code = normalize_token(self.cleaned_data['code'])
        if len(code) != TOKEN_LENGTH:
            raise forms.ValidationError(f'Der Wahlcode besteht aus {TOKEN_LENGTH} Zeichen.')
        try:
            self.student = Student.objects.get(token=code)
        except Student.DoesNotExist:
            raise forms.ValidationError('Dieser Wahlcode ist nicht bekannt. Bitte prüfe deine Eingabe.')
        return code


class ChoiceForm(forms.Form):
    """Up to three different wishes. All available wishes (max. 3) are required."""

    def __init__(self, *args, clubs=None, **kwargs):
        super().__init__(*args, **kwargs)
        clubs = clubs if clubs is not None else Club.objects.all()
        required = min(3, clubs.count())
        for i in range(1, 4):
            self.fields[f'choice{i}'] = forms.ModelChoiceField(
                queryset=clubs,
                required=i <= required,
                label=f'{i}. Wunsch',
                empty_label='– bitte wählen –',
                widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
            )

    def clean(self):
        cleaned = super().clean()
        picked = [cleaned.get(f'choice{i}') for i in range(1, 4)]
        picked = [c for c in picked if c is not None]
        if len(picked) != len(set(picked)):
            raise forms.ValidationError('Bitte wähle drei verschiedene AGs.')
        return cleaned


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'leader', 'max_size', 'order', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name der AG'}),
            'leader': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leitung'}),
            'max_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'max.', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'Kurzbeschreibung für die Wahlseite (optional)',
            }),
        }


class ClubSettingForm(forms.ModelForm):
    class Meta:
        model = ClubSetting
        fields = ['title', 'intro_text', 'voting_open', 'show_assignment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'intro_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'voting_open': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'show_assignment': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['last_name', 'first_name', 'group', 'assigned']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV-Datei', required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv,.txt,text/csv'}),
    )
    pasted = forms.CharField(
        label='… oder Daten einfügen', required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace', 'rows': 6,
            'placeholder': 'Nachname;Vorname;Klasse\nMustermann;Max;7a\nMusterfrau;Erika;7b',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('csv_file') and not (cleaned.get('pasted') or '').strip():
            raise forms.ValidationError('Bitte eine Datei auswählen oder Daten einfügen.')
        return cleaned
