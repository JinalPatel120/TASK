
from dataclasses import dataclass
import uuid
from django.db import models
from typing import Optional



@dataclass(frozen=True)
class UserID:
    """
    This is a value object that should be used to generate and pass the UserID to the UserFactory.
    """
    value: uuid.UUID


# ----------------------------------------------------------------------
# User Model
# ----------------------------------------------------------------------

class User(models.Model):
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

    class Meta:
        db_table = "user"


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
        last_name: str ,
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
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional[User]:
        """
        This method finds a user by their username from the actual database.
        """
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None
        
    @classmethod
    def find_by_email(cls,email:str) -> Optional[User]:
        """
        This method finds a user by their username from the actual database.
        """
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            return None

