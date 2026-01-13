from django.conf import settings

from email_config.models import EmailConfig


def apply_email_config():
    try:
        config = EmailConfig.objects.filter(is_active=True, is_default=True).first()
        if config:
            settings.EMAIL_HOST = config.host
            settings.EMAIL_PORT = config.port
            settings.EMAIL_HOST_USER = config.username
            settings.EMAIL_HOST_PASSWORD = config.password
            settings.EMAIL_USE_TLS = config.use_tls
            settings.DEFAULT_FROM_EMAIL = config.username
    except Exception as e:
        # Optionally log the error
        pass


def mask_secret(value: str) -> str:
    """Return a masked version of a secret for safe display in API responses.

    Keeps a short prefix/suffix visible for identification while hiding the
    middle characters. Very short values are fully masked.
    """
    try:
        if not value:
            return value
        s = str(value)
        n = len(s)
        if n <= 6:
            return "*" * n
        # show first 3 and last 3 characters, mask the rest
        return s[:3] + "*" * (n - 6) + s[-3:]
    except Exception:
        return "***"
