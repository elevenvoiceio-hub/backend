from django.urls import path
from .views import (
    SubscriptionPlanView,
    AssignSubscription,
    RevokeSubscription,
    SubscribeUser,
    CheckOwnSubscription,
    CheckUserSubscriptionByAdmin,
    GetDefaultCharacterLimit,
)
from .statistics import SystemStatisticsView

urlpatterns = [
    path("", SubscriptionPlanView.as_view()),
    path("assign/", AssignSubscription.as_view()),
    path("revoke/", RevokeSubscription.as_view()),
    path("subscribe/", SubscribeUser.as_view()),
    path(
        "check/<int:user_id>/",
        CheckUserSubscriptionByAdmin.as_view(),
        name="check-user-subscription",
    ),
    path("me/", CheckOwnSubscription.as_view(), name="check-own-subscription"),
    path(
        "default-character-limit/<int:user_id>/",
        GetDefaultCharacterLimit.as_view(),
        name="default-character-limit",
    ),
    path("statistics/", SystemStatisticsView.as_view(), name="system-statistics"),
]
