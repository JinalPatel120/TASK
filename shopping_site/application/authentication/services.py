#shopping_site/application/authentication/services.py
from shopping_site.domain.authentication.models import User
from shopping_site.domain.authentication.services import UserServices
from typing import Dict,Optional
from django.db import IntegrityError
from django.conf import settings
from django.core.mail import send_mail
import random
from django.utils import timezone
from datetime import timedelta,datetime
    
class UserApplicationService:
    """
    Application service class that interacts with the domain layer for user-related operations.
    """
    @staticmethod
    def register_user(user_data: Dict[str, str]) -> User:
        """
        This method handles the registration logic in the domain layer, including validation.
        It uses the UserServices class to handle user creation.
        """
        # Extract user data
        username = user_data['username']
        email = user_data['email']
        password = user_data['password']
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')

        
        if User.objects.filter(email=email).exists():
            return "A user with this email address already exists."
        if User.objects.filter(username=username).exists():
            return "A user with this username already exists."


        # Call UserServices to create the user and return the created user object
        user = UserServices.get_user_factory().build_entity_with_id(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
 
        try:
            # Save the user to the database
            user.save()
        except IntegrityError as e:
            # Catch the integrity error (e.g., duplicate email constraint violation)
            if 'user_email_key' in str(e):
                return "A user with this email address already exists."
            elif 'user_username_key' in str(e):
                return "A user with this username already exists."
            else:
                # Handle any other integrity errors
                return f"An error occurred: {str(e)}"

        return user
    

    @staticmethod
    def login_user(credentials: dict) -> Optional[dict]:
        username = credentials.get("username")
        password = credentials.get("password")
        try:
            user = UserServices.get_user_by_username(username)
            if user.password == password:  
                return {
                    "email": user.email,
                    "password": user.password
                }
        except User.DoesNotExist:
            return None  

        return None

    @staticmethod
    def request_password_reset(email):
        try:
            # Attempt to retrieve the user by email
            User.objects.get(email=email)
            return {"success": True}  # User found
        except User.DoesNotExist:
            # Return a dictionary indicating failure
            return {"success": False, "error_message": "User with this email does not exist. please Register First !"}

    @staticmethod
    def generate_and_send_otp(request,email):
        otp = str(random.randint(100000, 999999))
        expiration_time = timezone.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
        
        # Save OTP and expiration time to session (or database)
        UserApplicationService.save_otp(request, email, otp, expiration_time)
        
        # Send OTP to the user via email
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        return otp
    @staticmethod
    def save_otp(request, email, otp, expiration_time):
         # Save OTP and its expiration time in the session (or a database)
        session_key = f"otp_{email}"  # Create a unique session key based on email
        print(session_key)
        session_data = {
            'otp': otp,
            'expiration_time': expiration_time.isoformat(),  # Convert to string for JSON serialization
        }
        # Store OTP and expiration time in the session
        request.session[session_key] = session_data


    @staticmethod
    def verify_otp(request, email, otp):
        # Retrieve OTP and expiration time from session
        session_key = f"otp_{email}"  # Unique key for the user's OTP session data
        session_data = request.session.get(session_key)
        if not session_data:
            return False
        
        stored_otp = session_data.get('otp')
        expiration_time_str = session_data.get('expiration_time')
        expiration_time = datetime.fromisoformat(expiration_time_str)

        
        # Check if OTP matches and if it has expired
        if stored_otp == otp and timezone.now() < expiration_time:
            return True
        return False


    @staticmethod
    def reset_password(email, new_password):
        user = User.objects.get(email=email)
        user.password = new_password 
        user.save()
