from rest_framework import serializers

from model_voices_app.models import Voice


class VoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voice
        fields = [
            "id",
            "language",
            "language_code",
            "voice_code",
            "voicename",
            "voice_id",
            "gender",
            "updated_on",
            "sample_url",
            "style_list",
            "is_active",
            "model",
        ]
