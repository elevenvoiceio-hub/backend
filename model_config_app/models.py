from django.db import models


class Configuration(models.Model):
    provider = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    api_key = models.TextField()
    # Multiplier to apply when counting tokens/credits consumed by this model
    # Expected to be greater than 1.0
    token_multiplier = models.FloatField(default=1.0)
    active = models.BooleanField(default=True)
    is_stt = models.BooleanField(default=False)
    is_tts = models.BooleanField(default=False)
    is_clone = models.BooleanField(default=False)
    credits_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider} - {self.model_name}"
