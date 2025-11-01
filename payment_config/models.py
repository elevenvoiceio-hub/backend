from django.db import models


# Create your models here.
class PaymentConfig(models.Model):
    """
    Model to store payment configuration settings.
    """

    provider = models.CharField(
        max_length=50, help_text="Payment service provider (e.g., Stripe, PayPal)"
    )
    secret_key = models.CharField(
        max_length=255, help_text="Secret key for the payment provider"
    )
