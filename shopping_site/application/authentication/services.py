#shopping_site/application/authentication/services.py
from shopping_site.domain.authentication.models import User,OTP
from shopping_site.domain.authentication.services import UserServices
from typing import Dict,Optional
from django.db import IntegrityError
from django.conf import settings
from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from shopping_site.infrastructure.logger.models import AttributeLogger,logger
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta,datetime
import jwt
from django.db.models import Q

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

   

        # Combine the conditions to check for both email and username at once
        user_exists = User.objects.filter(Q(email=email) | Q(username=username)).first()
        if user_exists:
            # Log the specific error based on which field exists
            if user_exists.email == email:
                self.log.error(f"Registration failed: User with email {email} already exists.")
                return "A user with this email address already exists."
            if user_exists.username == username:
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

    def login_user(self, credentials: dict, request) -> Optional[User]:
        username = credentials.get("username")
        password = credentials.get("password")

        # Ensure both fields are provided
        if not username or not password:
            self.log.warning(f"Login failed: Missing username or password.")
            raise ValidationError("Both fields are required.")

        try:
            self.log.info(f"Attempting to authenticate user {username}.")
            user = authenticate(username=username, password=password)

            if user is not None:
                self.log.info(f"User {username} authenticated successfully.")
                login(request, user) 
                return user
            else:
                self.log.warning(f"Login failed: Incorrect username or password for user {username}.")
                return None
                 
        except User.DoesNotExist:
            self.log.error(f"Login failed: User with username {username} does not exist.")
            return None
        
    def generate_token(self, email: str, expiration_minutes=10) -> str:
        """
        Generates a JWT token for password reset with an expiration time.
        """
        expiration_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)  # 10 minutes expiration
        payload = {"email": email, "exp": expiration_time}
        return jwt.encode(payload, "jinal123", algorithm="HS256")

    def decode_token(self, token: str):
        """
        Decodes and validates the JWT token. Returns a tuple of decoded payload or error message.
        """
        try:
            payload = jwt.decode(token, "jinal123", algorithms=["HS256"])
            return payload, None  # Return the decoded payload if valid
        except jwt.ExpiredSignatureError:
            return None, "The link has expired. Please request a new OTP."
        except jwt.InvalidTokenError:
            return None, "Invalid token."
  
    def request_password_reset(self,email):
        try:
            # Attempt to retrieve the user by email
            UserServices.get_user_by_email(email=email)
            self.log.info(f"Password reset request received for email: {email}")
            return {"success": True}  
        except User.DoesNotExist:
            self.log.error(f"Password reset failed: User with email {email} does not exist.")
            return {"success": False, "error_message": "User with this email does not exist. please Register First !"}

    

    
    # Retrieve and convert the datetime object from the session
    # def get_otp_generated_time(self,request):
    #     otp_generated_time_str = request.session.get("otp_generated_time")
    #     if otp_generated_time_str:
    #         otp_generated_time = timezone.datetime.fromisoformat(otp_generated_time_str)
    #         return otp_generated_time
    #     return None
    

    # def save_otp(self,request, email, otp, expiration_time):
    #     try:
    #         user = UserServices.get_user_by_email(email=email)
            
    #         # Check if an OTP entry already exists for the user
    #         OTP.objects.update_or_create(
    #             user=user,
    #             defaults={
    #                 'otp': otp,
    #                 'expiration_time': expiration_time,
    #                 'created_at': timezone.now() 
    #             }
    #         )     
    #         self.log.info(f"OTP saved for user {email}")
    #     except User.DoesNotExist:
    #         self.log.error(f"User with email {email} does not exist.")



    # def verify_otp(self, request, email, token, otp):
    #     try:
    #         # Fetch the token from the session
    #         session_token = request.session.get('reset_token')

    #         # Fetch the token from the database (latest token for the user)
    #         otp_token = OTPToken.objects.filter(user__email=email, token=session_token).order_by('-created_at').first()

    #         if not otp_token:
    #             self.log.warning(f"Token does not exist or is invalid for email {email}.")
    #             return False

    #         self.log.info(f"Token found for email {email}")

    #         # Check if the token has expired
    #         if timezone.now() > otp_token.expiration_time:
    #             self.log.warning(f"OTP Token has expired for user {email}.")
    #             return False

    #         # Check if the user exists
    #         try:
    #             user = User.objects.get(email=email)
    #         except User.DoesNotExist:
    #             self.log.error(f"User with email {email} does not exist.")
    #             return False

    #         # Retrieve the most recent OTP record for the user
    #         otp_record = OTP.objects.filter(user=user).order_by('-created_at').first()

    #         self.log.info(f"OTP Record: OTP for {email} - {otp_record.otp}")
    #         self.log.info(f"Provided OTP: {otp}")
    #         self.log.info(f"OTP Expiry Time: {otp_record.expiration_time}")
    #         self.log.info(f"token as otp : {token}")

    #         # Validate OTP
    #         if otp_record and otp_record.otp == otp and timezone.now() < otp_record.expiration_time:
    #             self.log.info(f"OTP verification successful for user {email}")
    #             return True
    #         else:
    #             self.log.warning(f"OTP verification failed for user {email}. OTP might be incorrect or expired.")
    #             return False

    #     except Exception as e:
    #         self.log.error(f"Error verifying OTP for email {email}: {str(e)}")
    #         return False


    
    def generate_and_send_otp(self, email, token):
        otp = str(random.randint(100000, 999999))  # 6 digit OTP
        expiration_time = timezone.now() + timedelta(minutes=5)  # OTP expires in 5 minutes

        # Save OTP and token in the database
        self.save_otp(email, otp, expiration_time, token)

        # Send OTP to email
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}. Use this token to verify your OTP: {token}',
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )

        return otp

    def save_otp(self, email, otp, expiration_time, token):
        user = User.objects.get(email=email)
        
        print('user save otp',user)
        print('token save otp',token)
        # Create or update the OTP entry for the user
        otp_entry, created = OTP.objects.update_or_create(
            user=user,
             # Store the token in the OTP model
            defaults={
                'otp': otp,
                'token':token, 
                'expiration_time': expiration_time,
                'attempts': 0,  # Reset attempts for new OTP
                'created_at': timezone.now()
            }
        )
        return otp_entry

    def verify_otp(self, email, otp, token):
        try:
            otp_entry = OTP.objects.get(user__email=email, token=token)

            # Check if OTP is expired
            if otp_entry.is_expired():
                return {"success": False, "message": "OTP has expired."}

            # Check if OTP matches and attempts are less than 3
            if otp_entry.otp == otp:
                if otp_entry.attempts >= 3:
                    return {"success": False, "message": "Too many attempts. Please request a new OTP."}
                else:
                    otp_entry.reset_attempts()  # Reset attempts on success
                    return {"success": True, "message": "OTP verified successfully."}
            else:
                otp_entry.increment_attempts()  # Increment attempts on failure
                attempts_left = 3 - otp_entry.attempts
                if otp_entry.attempts >= 3:
                    return {"success": False, "message": "Too many failed attempts. Please request a new OTP."}
                else:
                    return {"success": False, "message": f"Invalid OTP. You have {attempts_left} attempts left."}

        except OTP.DoesNotExist:
            return {"success": False, "message": "Invalid token or OTP."}


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


    def handle_otp_attempts(self, request):
        """
        Handle OTP attempts, including blocking, resetting attempts, and calculating next retry time.
        """
        attempts = request.session.get("otp_attempts", 0)
        next_attempt_time = request.session.get("next_attempt_time")

        if attempts >= 3:
            if next_attempt_time:
                next_attempt_time = timezone.fromisoformat(next_attempt_time)
                if timezone.now() < next_attempt_time:
                    remaining_time = next_attempt_time - timezone.now()
                    remaining_seconds = int(remaining_time.total_seconds())
                    minutes = remaining_seconds // 60
                    seconds = remaining_seconds % 60
                    remaining_message = f"{minutes} minute(s) {seconds} second(s)" if minutes > 0 else f"{seconds} seconds"
                    return {
                        "is_disabled": True,
                        "remaining_message": remaining_message,
                        "next_attempt_time_seconds": remaining_seconds
                    }

        return None

    def increment_otp_attempts(self, request):
        """
        Increment the OTP attempts in the session.
        """
        attempts = request.session.get("otp_attempts", 0) 
        attempts +=1
        request.session["otp_attempts"] = attempts
        return attempts

    def set_next_attempt_time(self, request, attempts):
        """
        Set the time for the next allowed attempt based on the number of failed attempts.
        """
        time_deltas = [30, 60, 300, 3600, 28800]  # in seconds
        next_attempt_seconds = time_deltas[min(attempts - 3, len(time_deltas) - 1)]
        next_attempt_time = timezone.now() + timedelta(seconds=next_attempt_seconds)
        request.session["next_attempt_time"] = next_attempt_time.isoformat()
        return next_attempt_seconds


  