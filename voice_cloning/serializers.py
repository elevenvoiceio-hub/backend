from rest_framework import serializers
from .models import VoiceClones


class VoiceClonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceClones
        fields = [
            "id",
            "user",
            "voice_cloning_model",
            "clone_name",
            "clone_id",
            "gender",
            "language",
        ]
        read_only_fields = ["id", "user"]
