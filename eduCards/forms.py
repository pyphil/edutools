from django.forms import ModelForm
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import CardsPage, Category, Card


class CardsPageForm(ModelForm):
    class Meta:
        model = CardsPage
        fields = ('title', 'description', 'is_active', 'order')
        labels = {
            'title': mark_safe(f'<strong>{_("Page Title")}</strong>'),
            'description': mark_safe(f'<strong>{_("Description")}</strong>'),
            'is_active': mark_safe(f'<strong>{_("Active")}</strong>'),
            'order': mark_safe(f'<strong>{_("Display Order")}</strong>'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'color', 'order')
        labels = {
            'name': mark_safe(f'<strong>{_("Category Name")}</strong>'),
            'description': mark_safe(f'<strong>{_("Description")}</strong>'),
            'color': mark_safe(f'<strong>{_("Color (Hex Code)")}</strong>'),
            'order': mark_safe(f'<strong>{_("Display Order")}</strong>'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CardForm(ModelForm):
    class Meta:
        model = Card
        fields = ('title', 'content', 'additional_info', 'attachment', 'order')
        labels = {
            'title': mark_safe(f'<strong>{_("Card Title")}</strong>'),
            'content': mark_safe(f'<strong>{_("Content")}</strong>'),
            'additional_info': mark_safe(f'<strong>{_("Additional Information")}</strong>'),
            'attachment': mark_safe(f'<strong>{_("Attachment")}</strong>'),
            'order': mark_safe(f'<strong>{_("Display Order")}</strong>'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

