from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from feedback.models import FeedbackTicket
from permissions import IsAdmin
from .models import UserSubscription
from model_voices_app.models import Voice
from model_config_app.models import Configuration

User = get_user_model()


class SystemStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        # Get current time and date ranges
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # User Statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active_user=True).count()
        total_subscribed = UserSubscription.objects.filter(is_active=True).count()
        today_subscribed = UserSubscription.objects.filter(
            start_date__gte=today_start, is_active=True
        ).count()
        week_subscribed = UserSubscription.objects.filter(
            start_date__gte=week_start, is_active=True
        ).count()

        # Voice Statistics
        active_voices = Voice.objects.filter(is_active=True).count()

        # Open Service Requests (Configuration entries that are active)
        active_models = Configuration.objects.filter(active=True).count()

        service_requests = FeedbackTicket.objects.filter(status="open").count()

        statistics = {
            "users": {
                "active": active_users,
                "total_subscribed": total_subscribed,
                "total": total_users,
                "today_subscribed": today_subscribed,
                "week_subscribed": week_subscribed,
            },
            "voices": {"active": active_voices},
            "service_request": {"open": service_requests},
            "models": {"active": active_models},
        }

        return Response(statistics)
