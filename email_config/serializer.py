from rest_framework import serializers
from .models import EmailConfig


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
