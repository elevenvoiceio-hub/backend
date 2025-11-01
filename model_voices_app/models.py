from django.db import models

from model_config_app.models import Configuration


class Voice(models.Model):
    id = models.AutoField(primary_key=True)
    language = models.CharField(max_length=50)
    language_code = models.CharField(max_length=20)
    voice_code = models.CharField(max_length=50)
    country = models.CharField(max_length=50, blank=True, null=True)
    voicename = models.CharField(max_length=100)
    voice_id = models.CharField(max_length=255)
    gender = models.CharField(max_length=20)
    updated_on = models.DateTimeField(auto_now=True)
    sample_url = models.URLField(max_length=500, blank=True, null=True)
    style_list = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    model = models.ForeignKey(
        Configuration, on_delete=models.CASCADE, related_name="voices"
    )

    def __str__(self):
        return f"{self.voicename} ({self.language})"

    def __str__(self):
        return f"{self.name} ({self.language})"
