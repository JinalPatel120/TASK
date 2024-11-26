# shopping_site/application/authentication/services.py
from shopping_site.domain.authentication.models import User, OTP, UserAddress
from shopping_site.domain.authentication.services import UserServices
from typing import Dict, Optional, Union
from django.db import IntegrityError
from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from shopping_site.infrastructure.logger.models import AttributeLogger, logger
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta, datetime
import jwt
from django.db.models import Q, Case, When, Count
from django.conf import settings
from django.http import HttpRequest
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist


class UserApplicationService:

    def __init__(self, log: AttributeLogger) -> None:
        self.log = log  # Store the logger instance

    def register_user(self, user_data: Dict[str, str]):
        """
        This method handles the registration logic, including validation and user creation.
        """
        # Extract user data
        username = user_data["username"]
        email = user_data["email"]
        password = make_password(user_data["password"])  # Hash the password
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")

        # Combine the conditions to check for both email and username at once
        user_exists = User.objects.filter(
            Q(email=email) | Q(username=username)
        ).aggregate(
            email_count=Count(Case(When(email=email, then=1))),
            username_count=Count(Case(When(username=username, then=1))),
        )
        error_message = (
            "A user with this email address already exists."
            if user_exists["email_count"] > 0
            else "A user with this username already exists."
        )
        log_error_message = (
            f"Registration failed: User with email {email} already exists."
            if user_exists["email_count"] > 0
            else f"Registration failed: User with username {username} already exists."
        )
        if user_exists["email_count"] > 0 or user_exists["username_count"] > 0:
            self.log.error(log_error_message)
            return error_message
        user = UserServices.get_user_factory().build_entity_with_id(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        try:
            # Save the user to the database
            user.save()
        except IntegrityError as e:
            # Catch the integrity error (e.g., duplicate email constraint violation)
            if "user_email_key" in str(e):
                self.log.error(
                    f"IntegrityError: A user with email {email} already exists."
                )
                return "A user with this email address already exists."
            elif "user_username_key" in str(e):
                self.log.error(
                    f"IntegrityError: A user with username {username} already exists."
                )
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
                self.log.warning(
                    f"Login failed: Incorrect username or password for user {username}."
                )
                return None

        except User.DoesNotExist:
            self.log.error(
                f"Login failed: User with username {username} does not exist."
            )
            return None

    def generate_token(self, email: str, expiration_minutes=10) -> str:
        """
        Generates a JWT token for password reset with an expiration time.
        """
        expiration_time = datetime.utcnow() + timedelta(
            minutes=expiration_minutes
        )  # 10 minutes expiration
        payload = {"email": email, "exp": expiration_time}
        return jwt.encode(
            payload, settings.SECRET_KEY_TOKEN, algorithm=settings.ALGORITHM
        )

    def decode_token(self, token: str) -> str:
        """
        Decodes and validates the JWT token. Returns a tuple of decoded payload or error message.
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY_TOKEN, algorithms=settings.ALGORITHM
            )
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "The link has expired. Please request a new OTP."
        except jwt.InvalidTokenError:
            return None, "Invalid token."

    def get_email_from_token(self, token: str) -> str:
        """
        Extracts the email from the JWT token.
        """
        payload, error = self.decode_token(token=token)
        if error:
            self.log.error(f"Token error: {error}")
            return None
        return payload.get("email")

    def request_password_reset(self, email: str) -> str:
        """
        Handles the password reset request for a user by validating if the user exists.
        """
        try:
            # Attempt to retrieve the user by email
            UserServices.get_user_by_email(email=email)
            self.log.info(f"Password reset request received for email: {email}")
            return {"success": True}
        except User.DoesNotExist:
            self.log.error(
                f"Password reset failed: User with email {email} does not exist."
            )
            return {
                "success": False,
                "error_message": "User with this email does not exist. please Register First !",
            }

    def generate_and_send_otp(
        self, email: str, token: str, resend: bool = False
    ) -> str:
        """
        Generates a 6-digit OTP, saves it in the database, and sends it to the user's email with an HTML template.
        """
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        expiration_time = timezone.now() + timedelta(minutes=5)

        # Save OTP in the database (assuming you have this method)
        self.save_otp(
            token=token, otp=otp, expiration_time=expiration_time, email=email
        )

        if resend:
            verification_url = None  # No URL for resend
        else:
            verification_url = self.generate_otp_verification_url(
                token
            )  # Generate URL for first OTP

        # Render the HTML email template
        email_body_html = render_to_string(
            "index1.html",
            {
                "otp": otp,
                "verification_url": verification_url,
            },
        )

        # Create the email message with the rendered HTML
        subject = "Your OTP Code"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [email]

        email_message = EmailMultiAlternatives(
            subject,
            email_body_html,  # Plain text message (can be None)
            from_email,
            to_email,
        )

        email_message.attach_alternative(email_body_html, "text/html")
        email_message.send()

        return otp

    def generate_otp_verification_url(self, token: str) -> str:
        """
        Generates a URL for OTP verification using the provided token.
        """

        return f"{settings.SITE_URL}/auth/verify_otp/?token={token}"

    def save_otp(
        self, email: str, otp: str, expiration_time: datetime, token: str
    ) -> OTP:
        """
        Saves or updates the OTP for a given user in the database.
        """
        user = User.objects.get(email=email)

        # Create or update the OTP entry for the user
        otp_entry = OTP.objects.update_or_create(
            user=user,
            defaults={
                "otp": otp,
                "token": token,
                "expiration_time": expiration_time,
                "attempts": 0,  # Reset attempts for new OTP
                "created_at": timezone.now(),
            },
        )
        return otp_entry

    def verify_otp(self, email: str, otp: str, token: str) -> dict:
        """
        Verifies the OTP entered by the user and handles failed attempts.
        """
        try:
            otp_entry = OTP.objects.get(user__email=email, token=token)

            if otp_entry.is_expired():
                return {"success": False, "message": "OTP has expired."}

            if otp_entry.otp == otp:
                if otp_entry.attempts >= 3:
                    return {
                        "success": False,
                        "message": "Too many attempts. Please request a new OTP.",
                    }
                else:
                    otp_entry.reset_attempts()
                    return {"success": True, "message": "OTP verified successfully."}
            else:
                otp_entry.increment_attempts()  # Increment attempts on failure
                attempts_left = 3 - otp_entry.attempts
                if otp_entry.attempts >= 3:
                    return {
                        "success": False,
                        "message": "Too many failed attempts. Please request a new OTP.",
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Invalid OTP. You have {attempts_left} attempts left.",
                    }

        except OTP.DoesNotExist:
            return {"success": False, "message": "Invalid token or OTP."}

    def reset_password(self, email: str, new_password: str) -> Union[None, dict]:
        """
        Resets the password of the user with the provided email address.
        """
        try:
            user = UserServices.get_user_by_email(email=email)
            hashed_password = make_password(new_password)
            user.password = hashed_password
            user.save()
            self.log.info(f"Password reset successfully for user {email}")
        except User.DoesNotExist:
            self.log.error(
                f"Password reset failed: User with email {email} does not exist."
            )
        except Exception as e:
            self.log.error(
                f"Unexpected error during password reset for user {email}: {str(e)}"
            )

    def invalidate_token(self, email: str):
        """
        Invalidate the token by setting it to null in the database.
        """
        # Assuming you have a model called OTP that stores the token and email
        otp_record = OTP.objects.filter(user__email=email).first()
        if otp_record:
            otp_record.token = None  # Set the token to null to invalidate it
            otp_record.save()
        else:
            raise Exception(f"No OTP record found for email {email}")

    def is_token_invalid(self, email: str) -> bool:
        """
        Check if the token for the provided email is invalid (either expired or already used).
        """
        otp_record = OTP.objects.filter(user__email=email).first()
        if otp_record and otp_record.token is None:
            return True  # Token is invalid
        return False

    def handle_otp_attempts(self, request: HttpRequest):
        """
        Handles the number of OTP attempts, blocking attempts if necessary and calculating the next retry time.
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
                    remaining_message = (
                        f"{minutes} minute(s) {seconds} second(s)"
                        if minutes > 0
                        else f"{seconds} seconds"
                    )
                    return {
                        "is_disabled": True,
                        "remaining_message": remaining_message,
                        "next_attempt_time_seconds": remaining_seconds,
                    }

        return None

    def increment_otp_attempts(self, request: HttpRequest):
        """
        Increment the OTP attempts in the session.
        """
        attempts = request.session.get("otp_attempts", 0)
        attempts += 1
        request.session["otp_attempts"] = attempts
        return attempts

    def set_next_attempt_time(self, request: HttpRequest, attempts: int) -> int:
        """
        Set the time for the next allowed attempt based on the number of failed attempts.
        """
        time_deltas = [30, 60, 300, 3600, 28800]  # in seconds
        next_attempt_seconds = time_deltas[min(attempts - 3, len(time_deltas) - 1)]
        next_attempt_time = timezone.now() + timedelta(seconds=next_attempt_seconds)
        request.session["next_attempt_time"] = next_attempt_time.isoformat()
        return next_attempt_seconds

    def get_or_create_address(self, user, address_data):
        try:
            address = UserAddress.objects.create(user=user, **address_data)
            self.log.info(f"New address created for user {user.username}")
            return address
        except Exception as e:
            self.log.error(
                f"Error retrieving or creating address for user {user.username}: {str(e)}"
            )
            raise

    def get_user_address(self, user):
        """
        Retrieve specific fields of the shipping address for a given user.
        """
        try:
            # Retrieve specific fields from the UserAddress model
            address_fields = UserAddress.objects.filter(user=user).values(
                "flat_building", "area","landmark","city","pincode"
            )


            if address_fields:
                logger.info(
                    f"Address found for user {user.username}: {address_fields[0]}"
                )
              
                return address_fields[
                    0
                ]  
            else:
                logger.error(f"No address found for user {user.username}.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving user address for {user.username}: {str(e)}")
            raise ValueError(f"Could not retrieve address for user {user.username}.")
        
    def get_user_addresses(self, user):
        """
        Retrieve all shipping addresses for a given user.
        """
        try:
            # Retrieve all addresses for the user
            address_fields = UserAddress.objects.filter(user=user).values(
                "id", "flat_building", "area","landmark","city","state", "pincode"
            )

            if address_fields:
                logger.info(f"Found {len(address_fields)} addresses for user {user.username}.")
                return address_fields  # Return all addresses
            else:
                logger.error(f"No addresses found for user {user.username}.")
                return []  # Return an empty list if no addresses are found
        except Exception as e:
            logger.error(f"Error retrieving user addresses for {user.username}: {str(e)}")
            raise ValueError(f"Could not retrieve addresses for user {user.username}.")


    def get_default_address(self, user):
        # Logic to retrieve the user's default address
        # You might want to check a flag or field in the database that indicates the default address.
        try:
            # Assuming you have an Address model with a `is_default` flag
            default_address = UserAddress.objects.filter(
                user=user, is_default=True
            ).first()
            if default_address is None:
                self.log.warning(f"No default address found for user: {user.username}")

            return default_address

        except Exception as e:
            self.log.error(f"Error fetching default address: {str(e)}")
            return None

    def set_default_address(self, user, user_address):
        try:
            # Check if the provided address is already the default
            if user_address.is_default:
                self.log.info(
                    f"Address {user_address.id} is already set as default for user {user.username}. No update needed."
                )
                return True  # No action needed if it's already the default

            # Set the provided UserAddress as the default
            user_address.is_default = True
            user_address.save()

            # Reset any other UserAddress instances to not default
            user.address.exclude(id=user_address.id).update(is_default=False)

            self.log.info(
                f"Address {user_address.id} set as default for user {user.username}"
            )
            return True
        except Exception as e:
            self.log.error(
                f"Error setting default address for user {user.username}: {str(e)}"
            )
            return False

    def update_address(self, user, address_data):
        try:
            # Check if the user already has an address
            address = UserAddress.objects.get(user=user)
            for field, value in address_data.items():
                setattr(address, field, value)
            address.save()
            self.log.info(f"Address updated for user {user.username}")
            return address
        except ObjectDoesNotExist:
            self.log.error(f"Address not found for user {user.username}")
            raise
        except Exception as e:
            self.log.error(f"Error updating address for user {user.username}: {str(e)}")
            raise

    def get_address_by_id(self, user, address_id):
        try:
            # Assuming Address is a model that stores shipping addresses
            return UserAddress.objects.filter(user=user, id=address_id).first()
        except Exception as e:
            self.log.error(f"Error fetching address: {str(e)}")
            return None
        
    def remove_address(self, address_id: int) -> bool:
        """
        Removes an address by its ID.

        Args:
            address_id (int): The ID of the address to remove.

        Returns:
            bool: True if the address was removed, False if not found.
        """
        try:
            address = UserAddress.objects.get(id=address_id)
            address.delete()
            return True
        except ObjectDoesNotExist:
            return False
