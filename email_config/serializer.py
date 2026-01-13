from rest_framework import serializers
from .models import EmailConfig
from VoiceAsService.utils import mask_secret


class EmailConfigSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmailConfig
        fields = [
            "id",
            "username",
            "password",
            "host",
            "port",
            "use_tls",
            "provider",
            "created_at",
            "updated_at",
            "is_active",
            "created_by",
            "is_default",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        pwd = data.get("password")
        if pwd:
            data["password"] = mask_secret(pwd)
        return data
