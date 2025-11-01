from django.db import models

# Create your models here.


class EmailConfig(models.Model):
    """
    Model to store email configuration settings.
    """

    username = models.CharField(max_length=255, help_text="SMTP username")
    password = models.CharField(max_length=255, help_text="SMTP password")
    host = models.CharField(max_length=255, help_text="SMTP host")
    port = models.IntegerField(help_text="SMTP port")
    use_tls = models.BooleanField(default=True, help_text="Use TLS for SMTP")
    provider = models.CharField(
        max_length=50, help_text="Email service provider (e.g., Gmail, SendGrid)"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")
    is_active = models.BooleanField(
        default=True, help_text="Is this configuration active?"
    )
    created_by = models.ForeignKey(
        "user_app.User",
        on_delete=models.CASCADE,
        related_name="email_configs_created",
        help_text="User who created this configuration",
    )
    is_default = models.BooleanField(
        default=False, help_text="Is this the default email configuration?"
    )

    def __str__(self):
        return f"EmailConfig for {self.username}"
