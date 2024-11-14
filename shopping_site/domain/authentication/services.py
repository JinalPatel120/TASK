#shopping_site/domain/authentication/services.py
from shopping_site.domain.authentication.models import UserFactory
from shopping_site.domain.authentication.models import User
from typing import Type
from django.db.models.manager import BaseManager

class UserServices:
    """
    Service class responsible for handling user-related operations.
    """

    @staticmethod
    def get_user_factory() -> Type[UserFactory]:
        """
        This method returns the UserFactory class for creating users.
        """
        return UserFactory

    @staticmethod
    def get_user_repo() -> BaseManager[User]:
        """
        This method returns the UserRepository for accessing user data.
        """
        return User.objects 
    
    def get_user_by_id(self, user_id: str) -> User:
        """
        This method retrieves a user by their ID using the UserRepository.
        """
        try:
            return User.objects.get(id=user_id)  
        except User.DoesNotExist:
            raise ValueError(f"User with ID {user_id} does not exist.")
        
    @classmethod
    def get_user_by_username(cls,username:str) ->User:
        return User.objects.get(username=username) 

    @classmethod
    def get_user_by_email(cls, email: str) -> User:
        """
        This method retrieves a user by their email using the UserRepository.
        """
        try:
            return User.objects.get(email=email)  
        except User.DoesNotExist:
            return (f"User with email {email} does not exist.")
        

    