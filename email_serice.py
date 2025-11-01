from django.core.mail import send_mail
from django.conf import settings

from VoiceAsService.utils import apply_email_config


def send_custom_email(subject, message, recipient_list, from_email=None):
    apply_email_config()
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )


# Example usage:
if __name__ == "__main__":
    send_custom_email(
        subject="Hello",
        message="This is a custom email.",
        recipient_list=["recipient@example.com"],
    )
