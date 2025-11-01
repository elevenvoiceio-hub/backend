from rest_framework import serializers
from .models import FeedbackTicket


class FeedbackTicketSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackTicket
        fields = "__all__"
        read_only_fields = ["ticket_id", "created_by", "created_on"]

    def get_created_by(self, obj):
        return (
            obj.created_by.email
            if obj.created_by and hasattr(obj.created_by, "email")
            else None
        )
