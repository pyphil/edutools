from django.forms import ModelForm
from django import forms
from django.utils.safestring import mark_safe
from .models import CardsPage, Category, Card


class CardsPageForm(ModelForm):
    class Meta:
        model = CardsPage
        fields = ('title', 'description', 'is_active', 'order')
        labels = {
            'title': mark_safe('<strong>Page Title</strong>'),
            'description': mark_safe('<strong>Description</strong>'),
            'is_active': mark_safe('<strong>Active</strong>'),
            'order': mark_safe('<strong>Display Order</strong>'),
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
            'name': mark_safe('<strong>Category Name</strong>'),
            'description': mark_safe('<strong>Description</strong>'),
            'color': mark_safe('<strong>Color (Hex Code)</strong>'),
            'order': mark_safe('<strong>Display Order</strong>'),
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
            'title': mark_safe('<strong>Card Title</strong>'),
            'content': mark_safe('<strong>Content</strong>'),
            'additional_info': mark_safe('<strong>Additional Information</strong>'),
            'attachment': mark_safe('<strong>Attachment</strong>'),
            'order': mark_safe('<strong>Display Order</strong>'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

