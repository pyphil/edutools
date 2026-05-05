from django.db import models
from django.contrib.auth.models import User


class CardsPage(models.Model):
    """A page that contains multiple categories of cards"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
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


class Category(models.Model):
    """A category within a Cards Page that groups related cards"""
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
    """An individual card within a category"""
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='cards'
    )
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Main content of the card")
    additional_info = models.TextField(
        blank=True, null=True,
        help_text="Additional information"
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


class CardsPageAccessToken(models.Model):
    ACCESS_VIEW = 'view'
    ACCESS_EDIT = 'edit'
    ACCESS_CHOICES = [
        (ACCESS_VIEW, 'View Only'),
        (ACCESS_EDIT, 'View & Create Cards'),
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
