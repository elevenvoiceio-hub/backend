from rest_framework import serializers
from .models import FeedbackTicket, TicketMessage


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


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source="sender.username")
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = ["id", "sender", "sender_name", "sender_role", "message", "created_at"]
        read_only_fields = ["sender", "ticket", "created_at"]

    def get_sender_role(self, obj):
        # dynamic logic to tell the UI if the sender is staff or the user
        return "Admin" if obj.sender.role in ["admin", "subadmin"] else "User"
