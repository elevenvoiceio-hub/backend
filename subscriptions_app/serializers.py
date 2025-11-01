from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription
from django.contrib.auth import get_user_model

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "plan_id",
            "name",
            "description",
            "price",
            "duration_days",
            "is_popular",
            "character_limit",
            "voice_limit",
            "default_character_limit",
            "features",
            "limitations",
            "old_price",
            "discount",
            "on_offer",
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription = SubscriptionPlanSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(),
        source="subscription",
        write_only=True,
        required=False,
    )
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True, required=False
    )

    class Meta:
        model = UserSubscription
        fields = [
            "id",
            "user",
            "user_id",
            "subscription",
            "subscription_id",
            "start_date",
            "end_date",
            "is_active",
            "payment_id",
            "character_credits",
            "voice_credits",
        ]


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subscription_id = serializers.IntegerField()
    payment_id = serializers.CharField()
