# shopping_site/domain/authentication/models.py
from dataclasses import dataclass
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import jwt
from django.utils import timezone


@dataclass(frozen=True)
class UserID:
    """
    This is a value object that should be used to generate and pass the UserID to the UserFactory.
    """

    value: uuid.UUID


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the custom user model.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email, password, and other required fields.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, email, password, **extra_fields)


# ----------------------------------------------------------------------
# User Model
# ----------------------------------------------------------------------


class User(AbstractUser):
    """
    Represents a User model in the Domain Layer.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    username = models.CharField(max_length=150, unique=True, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    # Activity tracking fields
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    last_login = None
    is_staff = None
    date_joined = None

    class Meta:
        db_table = "user"


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expiration_time

    def increment_attempts(self):
        self.attempts += 1
        self.save()

    def reset_attempts(self):
        self.attempts = 0
        self.save()


class UserFactory:
    """
    Factory class for creating User entities.
    """

    users_db = {}

    @classmethod
    def build_entity_with_id(
        cls,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """
        This is a factory method used for building an instance of User.
        A UserID is created when building the entity.
        """
        entity_id = UserID(uuid.uuid4())
        return cls.build_entity(
            id=entity_id,
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    @staticmethod
    def build_entity(
        id: UserID,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """
        This method creates a User entity using the provided fields.
        """
        return User(
            id=id.value,
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
