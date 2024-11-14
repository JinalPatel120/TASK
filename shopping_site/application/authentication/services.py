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
        password = make_password(user_data['password'])  # Hash the password
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
    def login_user(credentials: dict,request) -> Optional[dict]:
        username = credentials.get("username")
        password = credentials.get("password")
        try:
            if not username or not password:
                raise ValidationError("Both fields are required.")
            user = UserServices.get_user_by_username(username=username)
            
            # Use check_password to compare the entered password with the hashed password
            if check_password(password, user.password):
                return user
            else:
                print("Invalid password")
                return None
        except User.DoesNotExist:
            print("User not found")
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
        
        UserApplicationService.save_otp(request, email, otp, expiration_time)
        
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        return otp
    @staticmethod
    def save_otp(request, email, otp, expiration_time):
        try:
            user = User.objects.get(email=email)
            
            # Check if an OTP entry already exists for the user
            otp_record, created = OTP.objects.update_or_create(
                user=user,
                defaults={
                    'otp': otp,
                    'expiration_time': expiration_time,
                    'created_at': timezone.now()  # Update created_at to current time
                }
            )
            
            if created:
                print(f"New OTP saved for {email}")
            else:
                print(f"Existing OTP updated for {email}")
        except User.DoesNotExist:
            print(f"User with email {email} does not exist.")



    @staticmethod
    def verify_otp(request, email, otp):
        try:
            user = User.objects.get(email=email)
           
            otp_record = OTP.objects.filter(user=user).order_by('-created_at').first()

            if otp_record and otp_record.otp == otp and timezone.now() < otp_record.expiration_time:
                return True
            return False
        except User.DoesNotExist:
            return False


    @staticmethod
    def reset_password(email, new_password):
        user = User.objects.get(email=email)
        hashed_password = make_password(new_password)
        user.password = hashed_password
        user.save()
