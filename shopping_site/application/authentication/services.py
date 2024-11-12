from shopping_site.domain.authentication.models import User
from shopping_site.domain.authentication.models import UserFactory
from shopping_site.domain.authentication.services import UserService,LoginService,PasswordService
from typing import Dict,Optional



class UserApplicationService:
    """
    Application service class that interacts with the domain layer for user-related operations.
    """

    @staticmethod
    def register_user(user_data: Dict[str, str]) -> User:
        """
        This method is used by the interface layer (views) to register a new user.
        It calls the domain layer's UserService and UserFactory to handle the registration logic.
        """

        # Call the UserService to register the user
        user = UserService.register_user(user_data)

        # Save the user to the database
        user.save()

        return user
    

    @staticmethod
    def login_user(username: str, password: str) -> Optional[User]:
        """Authenticate the user using LoginService."""
        credentials = {
            "username": username,
            "password": password
        }

        return LoginService.authenticate_user(credentials)
    

class PasswordResetService:
    """
    Service class for handling password reset functionality without a token.
    """

    @staticmethod
    def request_password_reset(email: str) -> Optional[str]:
        """
        This method simulates a password reset request by sending a reset email.
        """

        user=PasswordService.validate_email_by_user(email) 
       
        return user

    


    @staticmethod
    def reset_password(email: str, new_password: str, confirm_password: str) -> Optional[str]:
        """
        This method resets the user's password directly after validating the email and password confirmation.
        """
        if new_password != confirm_password:
            return "Passwords do not match."
        
        if len(new_password) < 8:  # Example of password criteria: at least 8 characters
            return "Password must be at least 8 characters long."
        
        try:
            user = User.objects.get(email=email)
            user.password = new_password  # Ensure the new password is hashed
            user.save()
            return "Password successfully updated."
        except User.DoesNotExist:
            return "Invalid email address."
