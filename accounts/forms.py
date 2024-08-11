from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django import forms


class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2'
        )

    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['onchange'] = "this.value=this.value.toLowerCase()"
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class ChangeUsernameForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'username',
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the 'password' field from the form
        self.fields.pop('password')
