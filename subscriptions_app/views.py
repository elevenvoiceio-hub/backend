from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from permissions import IsAdminOrSubAdmin
from .models import SubscriptionPlan, UserSubscription
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscribeSerializer,
)

User = get_user_model()


class SubscriptionPlanView(APIView):
    # Anyone can view the subscription plans
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=SubscriptionPlanSerializer)
    def post(self, request):
        """Only Admins can create a subscription"""
        if not (request.user.role).lower() == "admin":
            return Response(
                {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=SubscriptionPlanSerializer)
    def put(self, request):
        """Only Admins can update a subscription"""
        if not (request.user.role).lower() == "admin":
            return Response(
                {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
            )

        try:
            plan = SubscriptionPlan.objects.get(id=request.data.get("id"))
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Only Admins can delete a subscription"""
        if not (request.user.role).lower() == "admin":
            return Response(
                {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
            )

        plan_id = request.data.get("id")
        if not plan_id:
            return Response(
                {"error": "Subscription plan id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        plan.delete()
        return Response(
            {"message": "Subscription plan deleted."}, status=status.HTTP_200_OK
        )


class AssignSubscription(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def post(self, request):
        try:
            user = User.objects.get(id=request.data.get("user_id"))
            plan = SubscriptionPlan.objects.get(id=request.data.get("subscription_id"))
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        duration = timedelta(days=plan.duration_days)
        end_date = timezone.now() + duration
        token_credits = plan.character_limit
        voice_credits = plan.voice_limit
        if UserSubscription.objects.filter(user=user, is_active=True).exists():
            return Response(
                {"error": "User already has an active subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UserSubscription.objects.create(
            user=user,
            subscription=plan,
            end_date=end_date,
            character_credits=token_credits,
            voice_credits=voice_credits,
        )
        return Response(
            {"message": "Subscription assigned."}, status=status.HTTP_200_OK
        )


class RevokeSubscription(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def post(self, request):
        try:
            user = User.objects.get(id=request.data.get("user_id"))
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        sub = UserSubscription.objects.filter(user=user, is_active=True).first()
        if sub:
            sub.is_active = False
            sub.save()
            return Response({"message": "Subscription revoked."})
        return Response(
            {"error": "Active subscription not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


class SubscribeUser(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=SubscribeSerializer)
    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data["email"])
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
                )

            if UserSubscription.objects.filter(user=user, is_active=True).exists():
                return Response(
                    {"error": "User already has an active subscription."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                plan = SubscriptionPlan.objects.get(
                    id=serializer.validated_data["subscription_id"]
                )
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {"error": "Subscription plan not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            duration = timedelta(days=plan.duration_days)
            end_date = timezone.now() + duration
            token_credits = plan.character_limit
            voice_credits = plan.voice_limit

            UserSubscription.objects.create(
                user=user,
                subscription=plan,
                end_date=end_date,
                payment_id=serializer.validated_data["payment_id"],
                character_credits=token_credits,
                voice_credits=voice_credits,
            )
            return Response(
                {"message": "Subscription successful."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckUserSubscriptionByAdmin(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        subscription = UserSubscription.objects.filter(
            user=user, is_active=True
        ).first()
        if subscription:
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"message": "No active subscription found."},
            status=status.HTTP_404_NOT_FOUND,
        )


class CheckOwnSubscription(APIView):
    """
    Checks if the authenticated user has an active subscription and returns
    subscription status along with the plan_id.
    Admins are always considered subscribed.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if the user is an admin.
        # Note: This assumes your custom User model has a 'role' attribute
        # as implied by your original code.
        if hasattr(user, 'role') and user.role and user.role.lower() == "admin":
            return Response(
                {
                    "subscribed": True,
                    "reason": "Admin has full access",
                    "plan_id": "admin_access"  # Providing a special ID for admin
                },
                status=status.HTTP_200_OK,
            )

        # For non-admin users, find their latest active subscription.
        # We use .order_by() and .first() to get the most recent one.
        active_subscription = UserSubscription.objects.filter(
            user=user, is_active=True
        ).order_by('-start_date').first()

        if active_subscription:
            # User has an active subscription
            return Response(
                {
                    "subscribed": True,
                    # Access the related subscription's plan_id
                    "plan_id": active_subscription.subscription.id,
                    "remainining_character_credits": active_subscription.character_credits,
                    "remaining_voice_credits": active_subscription.voice_credits,
                },
                status=status.HTTP_200_OK
            )
        else:
            # User does not have an active subscription
            return Response(
                {"subscribed": False, "plan_id": None},
                status=status.HTTP_200_OK
            )



class GetDefaultCharacterLimit(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        subscription = UserSubscription.objects.filter(
            user=user, is_active=True
        ).first()
        if not subscription or not subscription.subscription:
            return Response(
                {"error": "Active subscription not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        character_limit = getattr(
            subscription.subscription, "default_character_limit", None
        )
        if character_limit is None:
            return Response(
                {"error": "Character limit not set in subscription plan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"default_character_limit": character_limit}, status=status.HTTP_200_OK
        )
