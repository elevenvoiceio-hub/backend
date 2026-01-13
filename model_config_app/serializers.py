from rest_framework import serializers
from .models import Configuration
from VoiceAsService.utils import mask_secret


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = [
            "id",
            "provider",
            "model_name",
            "api_key",
            "token_multiplier",
            "active",
            "is_stt",
            "is_tts",
            "is_clone",
            "credits_used",
            "created_at",
            "updated_at",
        ]

    def validate_token_multiplier(self, value):
        """Ensure token_multiplier is strictly greater than 1."""
        try:
            if value is None:
                raise serializers.ValidationError(
                    "token_multiplier is required and must be greater than 1"
                )
            if not isinstance(value, (int, float)):
                raise serializers.ValidationError("token_multiplier must be a number")
            if value <= 1.0:
                raise serializers.ValidationError(
                    "token_multiplier must be greater than 1"
                )
        except TypeError:
            raise serializers.ValidationError("token_multiplier must be a number")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        api_key = data.get("api_key")
        if api_key:
            data["api_key"] = mask_secret(api_key)
        return data


class ToggleModelActivationSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    activate = serializers.BooleanField()
