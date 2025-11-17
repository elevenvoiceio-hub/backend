from django.utils import timezone
from subscriptions_app.models import UserSubscription


def is_admin(user):
    return getattr(user, "role", "") == "admin"


def is_sub_admin(user):
    return getattr(user, "role", "") == "subAdmin"


def check_user_subscription(user):
    """
    Check if the user has an active subscription.

    Args:
        user: The user object to check.

    Returns:
        bool: True if the user has an active subscription, False otherwise.
    """
    if user.is_authenticated:
        if is_admin(user) or is_sub_admin(user):
            return True
        subscription = UserSubscription.objects.filter(
            user=user, is_active=True
        ).first()
        if subscription:
            if (
                subscription.end_date > timezone.now()
                and subscription.character_credits > 0
            ):
                return True
    return False


def reduce_character_credits(user, characters_used):
    """
    Reduce the user's character credits based on the number of characters used.

    Args:
        user: The user object whose credits will be reduced.
        characters_used: The number of characters to reduce from the user's credits.

    Returns:
        bool: True if the credits were successfully reduced, False otherwise.
    """
    if user.is_authenticated:
        if is_admin(user) or is_sub_admin(user):
            return True
        subscription = UserSubscription.objects.filter(
            user=user, is_active=True
        ).first()
        if subscription and subscription.character_credits >= characters_used:
            subscription.character_credits -= characters_used
            subscription.save()
            return True
    return False


def increase_model_credits(credits_to_add, model):
    """
    Increase the model's credits based on the number of credits to add.

    Args:
        model: The model object whose credits will be increased.
        credits_to_add: The number of credits to add to the model's credits.

    Returns:
        bool: True if the credits were successfully increased, False otherwise.
    """
    if model:
        model.credits_used += credits_to_add
        model.save()
        return True
    return False
