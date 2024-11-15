#shopping_site/application/authentication/services.py
from shopping_site.domain.authentication.models import User,OTP
from shopping_site.domain.authentication.services import UserServices
from typing import Dict,Optional
from django.db import IntegrityError
from django.conf import settings
from django.core.mail import send_mail
import random
from django.utils import timezone
from datetime import timedelta,datetime
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth import login
from django.core.exceptions import ValidationError
import logging
from shopping_site.infrastructure.logger.models import AttributeLogger,logger
from django.contrib.auth import authenticate

class UserApplicationService:
    def __init__(self, log: AttributeLogger)-> None:
        self.log = log  # Store the logger instance

    def register_user(self, user_data: Dict[str, str]):
        """
        This method handles the registration logic, including validation and user creation.
        """
        # Extract user data
        username = user_data['username']
        email = user_data['email']
        password = make_password(user_data['password'])  # Hash the password
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')

        # Log if the email already exists
        if User.objects.filter(email=email).exists():
            self.log.error(f"Registration failed: User with email {email} already exists.")
            return "A user with this email address already exists."

        # Log if the username already exists
        if User.objects.filter(username=username).exists():
            self.log.error(f"Registration failed: User with username {username} already exists.")
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
                self.log.error(f"IntegrityError: A user with email {email} already exists.")
                return "A user with this email address already exists."
            elif 'user_username_key' in str(e):
                self.log.error(f"IntegrityError: A user with username {username} already exists.")
                return "A user with this username already exists."
            else:
                # Log any other integrity errors
                self.log.error(f"Unexpected IntegrityError: {str(e)}")
                return f"An error occurred: {str(e)}"

        # Log successful registration
        self.log.info(f"User {username} registered successfully.")
        return user


    # def login_user(self,credentials: dict,request) -> Optional[dict]:
    #     username = credentials.get("username")
    #     password = credentials.get("password")
    #     try:
    #         if not username or not password:
    #             self.log.warning(f"Login failed: Missing username or password.")
    #             raise ValidationError("Both fields are required.")
    #         user = UserServices.get_user_by_username(username=username)
            
    #         # Use check_password to compare the entered password with the hashed password
    #         if check_password(password, user.password):
    #             self.log.info(f"User {username} logged in successfully.")
    #             return user
    #         else:
    #             self.log.warning(f"Login failed: Incorrect password for user {username}.")
    #             return None
    #     except User.DoesNotExist:
    #         self.log.error(f"Login failed: User with username {username} does not exist.")
    #         return None
      


    def login_user(self, credentials: dict, request) -> Optional[User]:
        username = credentials.get("username")
        password = credentials.get("password")

        # Ensure both fields are provided
        if not username or not password:
            self.log.warning(f"Login failed: Missing username or password.")
            raise ValidationError("Both fields are required.")

        try:
            # Attempt to get the user
            user = User.objects.get(username=username)

            # Log the password hash check
            self.log.info(f"Checking password for user {username}.")
            if check_password(password, user.password):
                self.log.info(f"Password matched for user {username}.")
                
                # Authenticate the user
                authenticated_user = authenticate(username=username, password=password)
                if authenticated_user:
                    self.log.info(f"User {username} authenticated successfully.")
                    # You can also manually log the user in here if needed
                    login(request, authenticated_user)  # Make sure the user is logged in
                    return authenticated_user
                else:
                    self.log.warning(f"Authentication failed for user {username}.")
                    return None
            else:
                self.log.warning(f"Login failed: Incorrect password for user {username}.")
                return None

        except User.DoesNotExist:
            self.log.error(f"Login failed: User with username {username} does not exist.")
            return None

  
    def request_password_reset(self,email):
        try:
            # Attempt to retrieve the user by email
            UserServices.get_user_by_email(email=email)
            self.log.info(f"Password reset request received for email: {email}")
            return {"success": True}  
        except User.DoesNotExist:
            self.log.error(f"Password reset failed: User with email {email} does not exist.")
            return {"success": False, "error_message": "User with this email does not exist. please Register First !"}


    def generate_and_send_otp(self,request,email):
        otp = str(random.randint(100000, 999999))
        expiration_time = timezone.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
        
        UserApplicationService.save_otp(self,request, email, otp, expiration_time)
        
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        self.log.info(f"OTP generated and sent to {email}")
        return otp
    
    
    def save_otp(self,request, email, otp, expiration_time):
        try:
            user = UserServices.get_user_by_email(email=email)
            
            # Check if an OTP entry already exists for the user
            OTP.objects.update_or_create(
                user=user,
                defaults={
                    'otp': otp,
                    'expiration_time': expiration_time,
                    'created_at': timezone.now() 
                }
            )     
            self.log.info(f"OTP saved for user {email}")
        except User.DoesNotExist:
            self.log.error(f"User with email {email} does not exist.")


    def verify_otp(self,email, otp):
        try:
            user = UserServices.get_user_by_email(email=email)
            otp_record = OTP.objects.filter(user=user).order_by('-created_at').first()

            if otp_record and otp_record.otp == otp and timezone.now() < otp_record.expiration_time:
                self.log.info(f"OTP verification successful for user {email}")
                return True
            else:
                self.log.warning(f"OTP verification failed for user {email}. OTP might be incorrect or expired.")
                return False
          
        except User.DoesNotExist:
            self.log.error(f"OTP verification failed: User with email {email} does not exist.")
            return False



    def reset_password(self,email, new_password):
        """
        This method resets the user's password.
        """
        try:
            user = UserServices.get_user_by_email(email=email)
            hashed_password = make_password(new_password)
            user.password = hashed_password
            user.save()
            self.log.info(f"Password reset successfully for user {email}")
        except User.DoesNotExist:
            self.log.error(f"Password reset failed: User with email {email} does not exist.")
        except Exception as e:
            self.log.error(f"Unexpected error during password reset for user {email}: {str(e)}")

