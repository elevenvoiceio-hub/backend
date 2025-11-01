from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from django.db.models import Q

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    General user serializer for viewing user data.
    """

    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "is_active_user"]
        read_only_fields = ["id", "role", "is_active_user"]


class UpdateUserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user role.
    """

    class Meta:
        model = User
        fields = ["role"]

    def validate_role(self, value):
        valid_roles = dict(User.ROLE_CHOICES).keys()
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Choose from: {', '.join(valid_roles)}"
            )
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Stores either email, username, or both, along with password.
    """

    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(required=False, default="user")

    class Meta:
        model = User
        fields = ["email", "username", "password", "role"]

    def validate(self, attrs):
        email = attrs.get("email", "").strip()
        username = attrs.get("username", "").strip()

        if not email and not username:
            raise serializers.ValidationError(
                "Either email or username must be provided."
            )

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(help_text="Email")
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_input = attrs.get("login")
        password = attrs.get("password")

        if not login_input or not password:
            raise serializers.ValidationError("Both login and password are required.")

        try:
            user = User.objects.filter(Q(email=login_input)).first()
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid login credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        return user  # return the User instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a user's profile.
    Allows updating username. Email is read-only for security reasons.
    """

    class Meta:
        model = User
        fields = ["username", "email"]
        read_only_fields = ["email"]  # Keep email read-only for security
