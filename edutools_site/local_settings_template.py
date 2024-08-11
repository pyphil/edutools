# Change this file and save it as local_settings.py

# How to generate a new secret key:
# python manage.py shell
# >>> from django.core.management.utils import get_random_secret_key
# >>> get_random_secret_key()

SECRET_KEY = ''
DEBUG = False  # must be False in production
ALLOWED_HOSTS = ['']  # enter your hostname

EMAIL_USE_TLS = True
EMAIL_HOST = ''  # e.g. smtp.office365.com
EMAIL_PORT = 587   # e.g. 587 for TLS
EMAIL_HOST_USER = ''  # e.g. noreply@domain.com
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = ''  # e.g. noreply@domain.com
