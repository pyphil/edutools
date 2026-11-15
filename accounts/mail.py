"""Helpers for the e-mails sent by the account registration and password reset."""
import logging

from django.conf import settings

from WLANCodesWebApp.models import Config

logger = logging.getLogger(__name__)


def normalize_email(value):
    """Return the entered e-mail address stripped and in lower case."""
    return (value or '').strip().lower()


def post_email_ratelimit_key(field_name):
    """Build a django-ratelimit key that groups requests by the posted e-mail address."""
    def key(group, request):
        return normalize_email(request.POST.get(field_name)) or 'empty'
    return key


def get_config_value(name, attribute='setting'):
    """Return the stripped value of a Config entry, or '' if it does not exist."""
    config = Config.objects.filter(name=name).first()
    if config is None:
        return ''
    return (getattr(config, attribute) or '').strip()


def get_sender_address():
    """
    Sender address for account e-mails: the 'noreply-mail' Config entry,
    falling back to DEFAULT_FROM_EMAIL. Returns '' if neither is configured.
    """
    sender = get_config_value('noreply-mail') or (settings.DEFAULT_FROM_EMAIL or '').strip()
    if not sender:
        logger.error(
            "No sender address configured for account e-mails: set the Config entry "
            "'noreply-mail' or DEFAULT_FROM_EMAIL."
        )
    return sender


def use_https_for_links(request):
    return settings.EMAIL_LINKS_USE_HTTPS or request.is_secure()


def build_absolute_link(request, path):
    scheme = 'https' if use_https_for_links(request) else 'http'
    return f'{scheme}://{request.get_host()}{path}'
