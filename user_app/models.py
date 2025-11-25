from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("subadmin", "Subadmin"),
        ("user", "User"),
    )

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_active_user = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # email_verification_code = models.CharField(max_length=10, blank=True, null=True)
    # reset_password_code = models.CharField(max_length=10, blank=True, null=True)
    # is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # Note: password is required by default

    def __str__(self):
        return self.email


class FavoriteVoices(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_voices"
    )
    voice_id = models.ForeignKey(
        "model_voices_app.Voice", on_delete=models.CASCADE, related_name="favorited_by"
    )
