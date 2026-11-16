"""Wahlcodes: short random codes that identify a student without a login."""
import re
import secrets

# No 0/O, 1/I/L to avoid confusion when typing the code from a printed slip.
ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
TOKEN_LENGTH = 8


def generate_token():
    return ''.join(secrets.choice(ALPHABET) for _ in range(TOKEN_LENGTH))


def generate_unique_token(model, field='token'):
    while True:
        token = generate_token()
        if not model.objects.filter(**{field: token}).exists():
            return token


def normalize_token(raw):
    """Turn user input like ' k7f3-qx2m ' into 'K7F3QX2M'."""
    return re.sub(r'[\s\-_.]', '', raw or '').upper()


def format_token(token):
    if not token:
        return ''
    half = len(token) // 2
    return f'{token[:half]}-{token[half:]}'
