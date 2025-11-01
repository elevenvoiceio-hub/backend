import logging
import random
import string

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from subscriptions_app.models import UserSubscription
from email_serice import send_custom_email
from model_voices_app.models import Voice
from permissions import IsAdminOrSubAdmin, IsAdmin
from .models import FavoriteVoices, User
from .serializers import (
    UserSerializer,
    RegistrationSerializer,
    ProfileUpdateSerializer,
    LoginSerializer,
    UpdateUserRoleSerializer,
)
from django.db import DatabaseError

logger = logging.getLogger(__name__)


class UpdateUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        request_body=UpdateUserRoleSerializer,
        responses={
            200: UserSerializer,
            400: "Bad Request",
            403: "Permission Denied",
            404: "User not found",
        },
        operation_description="Update a user's role. Only accessible by admin users.",
    )
    def put(self, request, user_id):
        try:
            # Get the target user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Validate and update the role
            serializer = UpdateUserRoleSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                # Return updated user data
                return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            return Response(
                {"error": "An error occurred while updating the user role"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterUser(APIView):
    @swagger_auto_schema(request_body=RegistrationSerializer)
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            # Generate a random 6-digit code
            code = "".join(random.choices(string.digits, k=6))
            user.email_verification_code = code
            user.is_email_verified = False
            user.save(update_fields=["email_verification_code", "is_email_verified"])

            # Prepare email content
            subject = "Verify your email"
            message = f"Your verification code is: {code}"
            recipient_list = [user.email]

            # Send the email
            send_custom_email(subject, message, recipient_list)

            return Response(
                {
                    "message": "User registered successfully. Verification code sent to email."
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            # Handle the validation error
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error in RegisterUser: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginUser(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data

            if not user.is_email_verified:
                return Response(
                    {
                        "detail": "Email is not verified. Please verify your email before logging in."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.is_active_user = True
            user.save(update_fields=["is_active_user"])

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )

        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": "Login failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CreateUser(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(request_body=RegistrationSerializer)
    def post(self, request):

        data = request.data.copy()
        serializer = RegistrationSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ActiveUsersView(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def get(self, request):

        try:
            count = User.objects.filter(is_active_user=True).count()
            return Response({"active_users": count}, status=status.HTTP_200_OK)
        except DatabaseError:
            return Response(
                {"active_users": 0, "warning": "Database issue"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"active_users": 0, "warning": "Unexpected issue"},
                status=status.HTTP_200_OK,
            )


class UpdateProfile(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Update user profile information including optional password change",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User's username"
                ),
                "current_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Current password (required only for password change)",
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="New password (required only for password change)",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                examples={
                    "application/json": {
                        "message": "Profile updated successfully",
                        "data": {
                            "id": 1,
                            "username": "user123",
                            "email": "user@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {"error": "Current password is incorrect"}
                },
            ),
            401: "Authentication credentials were not provided",
        },
    )
    def put(self, request):
        try:
            current_password = request.data.get("current_password")
            new_password = request.data.get("new_password")

            # Handle password update if both passwords are provided
            if current_password and new_password:
                # Verify current password
                if not request.user.check_password(current_password):
                    return Response(
                        {"error": "Current password is incorrect"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Set new password
                request.user.set_password(new_password)
                request.user.save(update_fields=["password"])

                # Remove password fields from data before updating profile
                data = request.data.copy()
                data.pop("current_password", None)
                data.pop("new_password", None)

                serializer = ProfileUpdateSerializer(
                    request.user, data=data, partial=True
                )
            else:
                serializer = ProfileUpdateSerializer(
                    request.user, data=request.data, partial=True
                )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully"
                    + (
                        " with password change"
                        if current_password and new_password
                        else ""
                    ),
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetAllUsers(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def get(self, request):
        try:
            users = User.objects.all()
            user_data = []
            for user in users:
                serializer = UserSerializer(user)
                data = serializer.data

                # Check subscription status and tokens
                subscription = UserSubscription.objects.filter(user=user).first()
                if subscription:
                    data["is_subscribed"] = True
                    data["character_limit"] = getattr(
                        subscription, "character_limit", 0
                    )
                    data["voice_limit"] = getattr(subscription, "voice_limit", 0)
                    data["plan_name"] = (
                        subscription.subscription.name
                        if subscription.subscription
                        else "No Plan"
                    )
                else:
                    data["is_subscribed"] = False
                    data["character_limit"] = 0
                    data["voice_limit"] = 0
                    data["plan_name"] = "No Plan"

                user_data.append(data)

            return Response(user_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Unexpected error in GetAllUsers")
            return Response(
                {"detail": "Unable to fetch users at the moment."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GetUserByUsernameOrEmail(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def get(self, request):
        try:
            username = request.query_params.get("username")
            email = request.query_params.get("email")

            if not username and not email:
                return Response(
                    {"detail": "Please provide either a username or an email."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(Q(username=username) | Q(email=email)).first()

            if not user:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
                )

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Unexpected error in GetUserByUsernameOrEmail")
            return Response(
                {"detail": "Unable to retrieve the user at this time."},
                status=status.HTTP_400_BAD_REQUEST,  # Changed from 500 to 400
            )


class LogoutUser(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logs out the user and marks them as inactive."
    )
    def post(self, request):
        try:
            user = request.user
            user.is_active_user = False
            user.save(update_fields=["is_active_user"])

            return Response(
                {"detail": "User successfully logged out."}, status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"detail": "Logout failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeleteOwnAccount(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            user = request.user
            user.delete()
            return Response(
                {"message": "Your account has been deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to delete account.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeleteUserByAdmin(APIView):
    permission_classes = [IsAdminOrSubAdmin]

    def delete(self, request, user_id):
        try:
            if request.user.id == user_id:
                return Response(
                    {
                        "error": "You cannot delete your own account here. Use the self-delete API."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
                )

            user.delete()
            return Response(
                {"message": "User deleted successfully."}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": "Failed to delete user.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddFavoriteVoice(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Add a voice to user's favorites list",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["voice_id"],
            properties={
                "voice_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the voice to add to favorites",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Voice successfully added to favorites",
                examples={"application/json": {"message": "Voice added to favorites."}},
            ),
            400: openapi.Response(
                description="Bad request",
                examples={"application/json": {"error": "Voice ID is required."}},
            ),
            404: openapi.Response(
                description="Voice not found",
                examples={"application/json": {"error": "Voice not found."}},
            ),
        },
    )
    def post(self, request):
        voice_id = request.data.get("voice_id")
        if not voice_id:
            return Response(
                {"error": "Voice ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = request.user
            voice = Voice.objects.filter(id=voice_id).first()
            if not voice:
                return Response(
                    {"error": "Voice not found."}, status=status.HTTP_404_NOT_FOUND
                )
            FavoriteVoices.objects.create(user=user, voice_id=voice)
            return Response(
                {"message": "Voice added to favorites."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            user = request.user
            favorites = FavoriteVoices.objects.filter(user=user)
            voice_ids = [fav.voice_id.id for fav in favorites]
            return Response(
                {"favorite_voice_ids": voice_ids}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveFavoriteVoice(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Remove one or multiple voices from user's favorites list",
        responses={
            200: openapi.Response(
                description="Voices successfully removed from favorites",
                examples={
                    "application/json": {
                        "message": "Voices removed from favorites",
                    }
                },
            ),
            404: openapi.Response(
                description="None of the voices were found in favorites",
                examples={
                    "application/json": {
                        "error": "No favorite voice found.",
                    }
                },
            ),
        },
    )
    def delete(self, request, voice_id):

        try:
            user = request.user

            favorite = FavoriteVoices.objects.filter(
                user=user, voice_id__id=voice_id
            ).first()
            if favorite:
                favorite.delete()
                return Response(
                    {
                        "message": "Voices removed from favorites",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "error": "No favorite voice found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            return Response(
                {"error": "Failed to remove voices from favorites.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyEmailAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        try:
            user = User.objects.get(email=email, email_verification_code=code)
            user.is_email_verified = True
            user.email_verification_code = ""
            user.save(update_fields=["is_email_verified", "email_verification_code"])
            return Response(
                {"message": "Email verified successfully."}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid code or email."}, status=status.HTTP_400_BAD_REQUEST
            )


class ResetPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")
        if not all([email, code, new_password]):
            return Response(
                {"error": "Email, code, and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email=email, reset_password_code=code)
            user.set_password(new_password)
            user.reset_password_code = ""
            user.save(update_fields=["password", "reset_password_code"])
            return Response(
                {"message": "Password updated successfully."}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid code or email."}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
            # Generate a random 6-digit code
            code = "".join(random.choices(string.digits, k=6))
            user.reset_password_code = code
            user.save(update_fields=["reset_password_code"])

            subject = "Password Reset Request"
            message = f"Your password reset code is: {code}"
            recipient_list = [user.email]
            send_custom_email(subject, message, recipient_list)

            return Response(
                {"message": "Password reset code sent to your email."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetLoggedInUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResendPasswordOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
            # Generate a new random 6-digit code
            code = "".join(random.choices(string.digits, k=6))
            user.reset_password_code = code
            user.save(update_fields=["reset_password_code"])

            subject = "Password Reset Code Resend"
            message = f"Your password reset code is: {code}"
            recipient_list = [user.email]
            send_custom_email(subject, message, recipient_list)

            return Response(
                {"message": "Password reset code resent to your email."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
