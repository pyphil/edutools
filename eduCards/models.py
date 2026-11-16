from django.db import models
from django.contrib.auth.models import User


# Board background themes: key -> (label, CSS background value)
BACKGROUND_CHOICES = [
    ('ocean', 'Ozean'),
    ('sunset', 'Sonnenuntergang'),
    ('forest', 'Wald'),
    ('lavender', 'Lavendel'),
    ('peach', 'Pfirsich'),
    ('mint', 'Minze'),
    ('slate', 'Schiefer'),
    ('night', 'Nacht'),
    ('sand', 'Sand'),
    ('plain', 'Hellgrau'),
]

BACKGROUND_CSS = {
    'ocean': 'linear-gradient(135deg, #2b5876 0%, #4e4376 100%)',
    'sunset': 'linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%)',
    'forest': 'linear-gradient(135deg, #134e5e 0%, #71b280 100%)',
    'lavender': 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
    'peach': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
    'mint': 'linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)',
    'slate': 'linear-gradient(135deg, #485563 0%, #29323c 100%)',
    'night': 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
    'sand': 'linear-gradient(135deg, #e6dada 0%, #c9b8a8 100%)',
    'plain': '#eef1f5',
}

# Backgrounds on which the board header text should be dark
LIGHT_BACKGROUNDS = {'peach', 'mint', 'sand', 'plain', 'lavender'}

CARD_COLOR_CHOICES = [
    ('white', 'Weiß'),
    ('yellow', 'Gelb'),
    ('orange', 'Orange'),
    ('red', 'Rot'),
    ('pink', 'Rosa'),
    ('purple', 'Lila'),
    ('blue', 'Blau'),
    ('teal', 'Türkis'),
    ('green', 'Grün'),
    ('gray', 'Grau'),
]

CARD_COLOR_CSS = {
    'white': '#ffffff',
    'yellow': '#fff6c7',
    'orange': '#ffe2c2',
    'red': '#ffd6d6',
    'pink': '#ffdcef',
    'purple': '#e9ddff',
    'blue': '#d8e9ff',
    'teal': '#d0f4f0',
    'green': '#dcf5d8',
    'gray': '#e9ecef',
}


class CardsPage(models.Model):
    """A board ("page") that contains multiple columns of cards"""
    LAYOUT_COLUMNS = 'columns'
    LAYOUT_GRID = 'grid'
    LAYOUT_STREAM = 'stream'
    LAYOUT_CHOICES = [
        (LAYOUT_COLUMNS, 'Spalten'),
        (LAYOUT_GRID, 'Raster'),
        (LAYOUT_STREAM, 'Stream'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=16, blank=True, default='📌')
    layout = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default=LAYOUT_COLUMNS)
    background = models.CharField(max_length=20, choices=BACKGROUND_CHOICES, default='ocean')
    allow_comments = models.BooleanField(default=True)
    allow_reactions = models.BooleanField(default=True)
    require_approval = models.BooleanField(
        default=False,
        help_text="Cards created via QR access must be approved by a teacher."
    )
    show_author = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='created_cards_pages'
    )
    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_cards_pages',
        help_text="Teachers who can access this page besides the creator."
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='modified_cards_pages', null=True, blank=True
    )
    last_modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(
        default=0,
        help_text="Order for display (lower numbers appear first)"
    )

    class Meta:
        verbose_name = 'Cards Page'
        verbose_name_plural = 'Cards Pages'
        ordering = ['order', 'title']

    def __str__(self):
        return str(self.title)

    @property
    def background_css(self):
        return BACKGROUND_CSS.get(self.background, BACKGROUND_CSS['ocean'])

    @property
    def has_light_background(self):
        return self.background in LIGHT_BACKGROUNDS


class Category(models.Model):
    """A column within a board that groups related cards"""
    cards_page = models.ForeignKey(
        CardsPage, on_delete=models.CASCADE, related_name='categories'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(
        max_length=7, default='#009641',
        help_text="Hex color code (e.g., #009641)"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order within the page (lower numbers appear first)"
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['cards_page', 'order', 'name']
        unique_together = [['cards_page', 'name']]

    def __str__(self):
        return f"{str(self.cards_page)} - {str(self.name)}"


class Card(models.Model):
    """An individual card (post) within a column"""
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='cards'
    )
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Main content of the card")
    additional_info = models.TextField(
        blank=True, null=True,
        help_text="Additional information"
    )
    link_url = models.URLField(max_length=500, blank=True, default='')
    color = models.CharField(max_length=10, choices=CARD_COLOR_CHOICES, default='white')
    is_pinned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    author_name = models.CharField(max_length=80, blank=True, default='')
    guest_key = models.CharField(
        max_length=64, blank=True, default='', db_index=True,
        help_text="Identifies the anonymous author's browser session."
    )
    attachment = models.FileField(
        null=True, blank=True, upload_to="eduCards/attachments/"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='created_cards', null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='modified_cards', null=True, blank=True
    )
    last_modified = models.DateTimeField(auto_now=True)
    order = models.IntegerField(
        default=0,
        help_text="Order within the category (lower numbers appear first)"
    )

    class Meta:
        ordering = ['category', 'order', 'title']

    def __str__(self):
        return f"{str(self.category)} - {str(self.title)}"

    @property
    def color_css(self):
        return CARD_COLOR_CSS.get(self.color, CARD_COLOR_CSS['white'])

    @property
    def display_author(self):
        if self.author_name:
            return self.author_name
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.username
        return ''


class CardAttachment(models.Model):
    """Additional file attached to a card."""
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to="eduCards/attachments/")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created', 'id']

    def __str__(self):
        return self.file.name

    @property
    def filename(self):
        return self.file.name.rsplit('/', 1)[-1]


class CardComment(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=2000)
    author_name = models.CharField(max_length=80, blank=True, default='')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='card_comments'
    )
    guest_key = models.CharField(max_length=64, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created', 'id']

    def __str__(self):
        return f"{self.card.title}: {self.text[:30]}"

    @property
    def display_author(self):
        if self.author_name:
            return self.author_name
        if self.user:
            return self.user.get_full_name() or self.user.username
        return 'Gast'


class CardReaction(models.Model):
    """A 'like' on a card, one per user or anonymous session."""
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='reactions')
    voter_key = models.CharField(max_length=80)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['card', 'voter_key']]

    def __str__(self):
        return f"{self.card.title} ♥ {self.voter_key}"


class CardsPageAccessToken(models.Model):
    ACCESS_VIEW = 'view'
    ACCESS_EDIT = 'edit'
    ACCESS_CHOICES = [
        (ACCESS_VIEW, 'Nur ansehen'),
        (ACCESS_EDIT, 'Ansehen & Beiträge erstellen'),
    ]

    cards_page = models.ForeignKey(
        CardsPage, on_delete=models.CASCADE, related_name='access_tokens'
    )
    token = models.CharField(max_length=64, unique=True)
    access_level = models.CharField(max_length=10, choices=ACCESS_CHOICES, default=ACCESS_EDIT)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='created_cards_page_tokens'
    )
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cards Page Access Token'
        verbose_name_plural = 'Cards Page Access Tokens'
        ordering = ['cards_page', '-created']

    def __str__(self):
        return f"{self.cards_page.title} - {self.token[:12]}... ({self.get_access_level_display()})"
