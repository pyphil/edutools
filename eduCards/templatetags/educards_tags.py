from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.safestring import mark_safe

from ..sanitize import sanitize_html

register = template.Library()


@register.filter
def clean_html(value):
    """Render rich text from the editor safely (defence in depth for older content)."""
    return mark_safe(sanitize_html(value))


@register.filter
def ago(value):
    """'gerade eben' for fresh content, otherwise 'vor 5 Minuten'."""
    if not value:
        return ''
    if timezone.now() - value < timedelta(minutes=1):
        return 'gerade eben'
    return f'vor {timesince(value).split(",")[0]}'
