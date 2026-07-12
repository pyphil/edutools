from django import forms
from .models import Club, ClubChoice, StudentUpload


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'max_size', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'max_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ClubChoiceForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = ClubChoice
        fields = ['first_name', 'last_name', 'choice1', 'choice2', 'choice3']

    def clean_first_name(self):
        v = self.cleaned_data.get('first_name', '')
        return v.strip()

    def clean_last_name(self):
        v = self.cleaned_data.get('last_name', '')
        return v.strip()


class StudentUploadForm(forms.ModelForm):
    class Meta:
        model = StudentUpload
        fields = ['csv_file', 'notes']
