# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    plan_id = models.CharField(
        max_length=100,
    )
    price = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dictionary with keys 'monthly' and 'yearly' for price values",
    )
    description = models.TextField(
        help_text="Short description of the plan", blank=True, default=""
    )
    features = models.JSONField(
        default=list, blank=True, help_text="List of feature strings"
    )
    limitations = models.JSONField(
        default=list, blank=True, help_text="List of limitation strings"
    )
    # Keep old fields for compatibility if needed
    old_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration_days = models.IntegerField(default=0)
    is_popular = models.BooleanField(default=False)
    character_limit = models.IntegerField(
        default=0, help_text="Number of characters allowed for the plan"
    )
    voice_limit = models.IntegerField(
        default=0, help_text="Number of voice credits allowed for the plan"
    )
    default_character_limit = models.IntegerField(
        default=0, help_text="Default character limit for the plan"
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage for the plan",
    )
    on_offer = models.BooleanField(
        default=False, help_text="Is this plan currently on offer?"
    )

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    character_credits = models.IntegerField(
        default=0
    )  # number of credits assigned to the user
    voice_credits = models.IntegerField(
        default=0
    )  # number of credits assigned to the user
    # number of credits assigned to the user

    def __str__(self):
        return f"{self.user.email} - {self.subscription.name}"
