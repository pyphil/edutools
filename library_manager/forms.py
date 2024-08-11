from django.forms import ModelForm
from django import forms
from .models import InventoryItem, LibraryBorrowedItem, LibraryCategoryShelfmark


class InventoryItemForm(ModelForm):
    class Meta:
        model = InventoryItem
        fields = (
            'author',
            'title',
            'category_shelfmark',
            # 'status',
            'inventory_number',
            'notes',
        )
        labels = {
            'author': 'Autor:in',
            'title': 'Titel',
            'category_shelfmark': 'Bereich/Signatur',
            # 'status': 'Status',
            'inventory_number': 'Inventarnummer (automatisch)',
            'notes': 'Bemerkungen',
        }
        widgets = {
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category_shelfmark': forms.Select(attrs={'class': 'form-select', 'style': 'width: 40%'}),
            # 'status': forms.Select(attrs={'class': 'form-select', 'style': 'width: 40%'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control text-center', 'style': 'width: 100px'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }


class LibraryBorrowedItemsForm(ModelForm):
    class Meta:
        model = LibraryBorrowedItem
        fields = (
            'first_name',
            'surname',
            'school_class',
        )
        labels = {
            'first_name': 'Vorname',
            'surname': 'Nachname',
            'school_class': 'Klasse',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'school_class': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LibraryCategoryShelfmarkNewForm(ModelForm):
    class Meta:
        model = LibraryCategoryShelfmark
        fields = (
            'category',
            'shelfmark',
        )
        labels = {
            'category': 'Bereich',
            'shelfmark': 'Signatur',
        }
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'shelfmark': forms.TextInput(attrs={'class': 'form-control'}),
        }
