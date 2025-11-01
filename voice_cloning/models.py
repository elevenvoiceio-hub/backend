from django.db import models

from model_config_app.models import Configuration
from user_app.models import User


class VoiceClones(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voice_cloning_model = models.ForeignKey(Configuration, on_delete=models.CASCADE)
    clone_name = models.CharField(max_length=255, blank=True, null=True)
    clone_id = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        blank=True,
        null=True,
    )
    language = models.CharField(
        max_length=50, default="en", help_text="Language code (e.g., 'en' for English)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Voice Clone for {self.user.username} - {self.voice_cloning.model_name}"
