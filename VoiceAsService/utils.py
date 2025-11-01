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
