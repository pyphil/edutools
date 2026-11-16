import re

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import ModelForm
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import (
    BACKGROUND_CHOICES, BACKGROUND_CSS, CARD_COLOR_CHOICES, CARD_COLOR_CSS,
    CardsPage, Category, Card,
)
from .sanitize import sanitize_html

ALLOWED_UPLOAD_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'odt', 'ppt', 'pptx', 'odp', 'xls', 'xlsx', 'ods',
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'txt', 'zip', 'mp3', 'm4a', 'mp4',
}
MAX_UPLOAD_MB = 25

BOARD_TEMPLATES = [
    ('empty', 'Leeres Board', []),
    ('brainstorm', 'Brainstorming', [('Ideen', '#f59f00'), ('Fragen', '#1c7ed6'), ('Ergebnisse', '#2f9e44')]),
    ('kanban', 'Aufgaben (Kanban)', [('Zu erledigen', '#e03131'), ('In Arbeit', '#f59f00'), ('Erledigt', '#2f9e44')]),
    ('procon', 'Pro & Contra', [('Pro', '#2f9e44'), ('Contra', '#e03131'), ('Offene Fragen', '#868e96')]),
    ('week', 'Wochenplan', [('Montag', '#1c7ed6'), ('Dienstag', '#7048e8'), ('Mittwoch', '#d6336c'),
                            ('Donnerstag', '#f76707'), ('Freitag', '#2f9e44')]),
    ('feedback', 'Feedback', [('Das lief gut', '#2f9e44'), ('Das geht besser', '#f59f00'), ('Ideen & Wünsche', '#1c7ed6')]),
]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        items = data if isinstance(data, (list, tuple)) else [data]
        files = []
        for item in items:
            if item in (None, ''):
                continue
            uploaded = super().clean(item, initial)
            extension = uploaded.name.rsplit('.', 1)[-1].lower() if '.' in uploaded.name else ''
            if extension not in ALLOWED_UPLOAD_EXTENSIONS:
                raise forms.ValidationError(f'Der Dateityp von „{uploaded.name}“ ist nicht erlaubt.')
            if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                raise forms.ValidationError(f'„{uploaded.name}“ ist größer als {MAX_UPLOAD_MB} MB.')
            files.append(uploaded)
        return files


class SwatchSelect(forms.RadioSelect):
    """Radio buttons rendered as colour swatches (see templates)."""
    template_name = 'eduCards/widgets/swatch_select.html'
    option_template_name = 'eduCards/widgets/swatch_option.html'

    def __init__(self, css_map, *args, **kwargs):
        self.css_map = css_map
        super().__init__(*args, **kwargs)

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option['swatch'] = self.css_map.get(option['value'], '#fff')
        return option


class CardsPageForm(ModelForm):
    class Meta:
        model = CardsPage
        fields = (
            'icon', 'title', 'description', 'layout', 'background',
            'allow_reactions', 'allow_comments', 'require_approval', 'show_author', 'is_active',
        )
        labels = {
            'icon': 'Symbol',
            'title': 'Titel',
            'description': 'Beschreibung',
            'layout': 'Layout',
            'background': 'Hintergrund',
            'allow_reactions': 'Likes erlauben',
            'allow_comments': 'Kommentare erlauben',
            'require_approval': 'Beiträge von Schüler:innen erst nach Freigabe anzeigen',
            'show_author': 'Namen der Verfasser:innen anzeigen',
            'is_active': 'Board ist aktiv (deaktivierte Boards landen im Archiv)',
        }
        widgets = {
            'icon': forms.TextInput(attrs={'class': 'form-control text-center fs-4', 'maxlength': 4}),
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'z. B. Projektwoche 7b'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                 'placeholder': 'Worum geht es auf diesem Board?'}),
            'layout': forms.RadioSelect(),
            'allow_reactions': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'require_approval': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'show_author': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, with_template=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['background'].widget = SwatchSelect(BACKGROUND_CSS, choices=BACKGROUND_CHOICES)
        self.fields['icon'].required = False
        if with_template:
            del self.fields['is_active']
            self.fields['template'] = forms.ChoiceField(
                label='Vorlage',
                choices=[(key, label) for key, label, _ in BOARD_TEMPLATES],
                initial='empty',
                widget=forms.RadioSelect(),
            )

    def template_columns(self):
        key = self.cleaned_data.get('template', 'empty')
        for template_key, _, columns in BOARD_TEMPLATES:
            if template_key == key:
                return columns
        return []


class TeacherChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, user):
        full_name = user.get_full_name()
        return f'{full_name} ({user.username})' if full_name else user.username


class CardsPageShareForm(forms.Form):
    teachers = TeacherChoiceField(
        queryset=User.objects.filter(Q(is_staff=True) | Q(groups__name='teachers')).distinct().order_by('last_name', 'username'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        label='Mit Lehrkräften teilen',
        help_text='Mit Strg/Cmd lassen sich mehrere Lehrkräfte auswählen.',
    )


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'color')
        labels = {
            'name': 'Name der Spalte',
            'description': 'Beschreibung (optional)',
            'color': 'Farbe',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'z. B. Ideen'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }

    def __init__(self, *args, cards_page=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cards_page = cards_page or getattr(self.instance, 'cards_page', None)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if self.cards_page is not None:
            duplicates = Category.objects.filter(cards_page=self.cards_page, name__iexact=name)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError('Auf diesem Board gibt es bereits eine Spalte mit diesem Namen.')
        return name


class CardForm(ModelForm):
    content = forms.CharField(
        widget=CKEditor5Widget(config_name='extends'),
        label='Inhalt',
        required=False,
    )
    additional_info = forms.CharField(
        widget=CKEditor5Widget(config_name='extends'),
        label='Zusatzinfo zum Aufklappen (optional, z. B. Tipp oder Lösung)',
        required=False,
    )
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': ','.join('.' + ext for ext in sorted(ALLOWED_UPLOAD_EXTENSIONS)),
        }),
        label='Dateien',
        help_text=f'Mehrere Dateien gleichzeitig möglich (max. {MAX_UPLOAD_MB} MB pro Datei).',
    )

    class Meta:
        model = Card
        fields = ('title', 'content', 'additional_info', 'link_url', 'color', 'author_name', 'category')
        labels = {
            'title': 'Überschrift',
            'link_url': 'Link (optional)',
            'color': 'Kartenfarbe',
            'author_name': 'Dein Name',
            'category': 'Spalte',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Überschrift'}),
            'link_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://… (z. B. Webseite oder YouTube-Video)'}),
            'author_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname oder Gruppenname'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, cards_page=None, show_author_field=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['color'].widget = SwatchSelect(CARD_COLOR_CSS, choices=CARD_COLOR_CHOICES)
        self.fields['color'].required = False
        if cards_page is not None:
            self.fields['category'].queryset = cards_page.categories.order_by('order', 'name')
            self.fields['category'].empty_label = None
            self.fields['category'].label_from_instance = lambda category: category.name
            self.fields['category'].required = False
        else:
            del self.fields['category']
        if not show_author_field:
            del self.fields['author_name']
        else:
            self.fields['author_name'].required = False

    @staticmethod
    def _clean_rich_text(value):
        cleaned = sanitize_html(value or '')
        # an "empty" editor still submits markup like <p>&nbsp;</p>
        return cleaned if re.sub(r'<[^>]+>|&nbsp;|\xa0|\s', '', cleaned) else ''

    def clean_content(self):
        return self._clean_rich_text(self.cleaned_data.get('content'))

    def clean_additional_info(self):
        return self._clean_rich_text(self.cleaned_data.get('additional_info'))

    def clean_color(self):
        return self.cleaned_data.get('color') or 'white'

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('content') and not cleaned.get('link_url') and not cleaned.get('attachments') \
                and not (self.instance.pk and (self.instance.attachments.exists() or self.instance.attachment)):
            self.add_error('content', 'Bitte gib einen Text, einen Link oder eine Datei an.')
        return cleaned


class CommentForm(forms.Form):
    text = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'rows': 2}))
    author_name = forms.CharField(max_length=80, required=False)

