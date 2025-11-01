from rest_framework import serializers
from .models import Configuration


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "provider",
            "model_name",
            "api_key",
            "active",
            "is_stt",
            "is_tts",
            "is_clone",
            "credits_used",
            "created_at",
            "updated_at",
        ]


class ToggleModelActivationSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    activate = serializers.BooleanField()
