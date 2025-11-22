from django.db import models
from django.contrib.auth.models import User


class CardsPage(models.Model):
    """A page that contains multiple categories of cards"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cards_pages')
    created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modified_cards_pages', null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Order for display (lower numbers appear first)")

    class Meta:
        verbose_name = 'Cards Page'
        verbose_name_plural = 'Cards Pages'
        ordering = ['order', 'title']

    def __str__(self):
        return str(self.title)


class Category(models.Model):
    """A category within a Cards Page that groups related cards"""
    cards_page = models.ForeignKey(CardsPage, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#009641', help_text="Hex color code (e.g., #009641)")
    order = models.IntegerField(default=0, help_text="Order within the page (lower numbers appear first)")
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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Main content of the card")
    additional_info = models.TextField(blank=True, null=True, help_text="Additional information")
    attachment = models.FileField(null=True, blank=True, upload_to="eduCards/attachments/")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cards')
    created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modified_cards', null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0, help_text="Order within the category (lower numbers appear first)")

    class Meta:
        ordering = ['category', 'order', 'title']

    def __str__(self):
        return f"{str(self.category)} - {str(self.title)}"

