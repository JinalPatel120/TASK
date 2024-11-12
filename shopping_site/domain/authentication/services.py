from shopping_site.domain.authentication.models import UserFactory
from shopping_site.domain.authentication.models import User
from typing import Dict,Optional
from django.contrib.auth.hashers import check_password


class UserService:
    """
    Service class responsible for handling user-related operations, such as user registration.
    """

    @staticmethod
    def register_user(user_data: Dict[str, str]) -> User:
        """
        This method handles the registration of a new user.
        It uses the UserFactory to build a new User entity and return it.
        """

        # Extract data from the provided dictionary
        username = user_data["username"]
        email = user_data["email"]
        password = user_data["password"]
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # Use the UserFactory to create a new User entity
        user = UserFactory.build_entity_with_id(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        return user



class LoginService:
    """
    Service class responsible for handling user login operations, such as authenticating the user.
    """

    @staticmethod
    def authenticate_user(credentials: Dict[str, str]) -> Optional[User]:
        """
        This method handles the login of an existing user.
        It verifies the user's username and password.
        """
        username = credentials["username"]
        password = credentials["password"]

        user = UserFactory.find_by_username(username)  # This assumes you have a method to fetch the user by username
        if user:
            if password == user.password:
                return user
            else:
                return None
        else:
            return None
        

class PasswordService:


    @staticmethod
    def validate_email_by_user(email:Dict[str,str]) -> Optional[User]:
        user=UserFactory.find_by_email(email)
        if user:
            if email ==user.email:
                return user
            else:
                return None
        return user


