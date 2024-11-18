from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError, HttpResponseRedirect
from .forms import (
    RegistrationForm,
    UserLoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    OTPVerificationForm,
)
from shopping_site.application.authentication.services import UserApplicationService
from django.contrib import messages
from django.views.generic import TemplateView
from shopping_site.infrastructure.logger.models import logger
from datetime import timedelta,datetime
from django.utils import timezone
import jwt
import datetime



class RegisterView(FormView):
    """
    Class-based view to handle user registration.
    """

    template_name = "register.html"
    form_class = RegistrationForm
    success_url = "login"  # The URL to redirect after successful registration

    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
            # Get cleaned data from form
            cleaned_data = form.cleaned_data

            user_data = {
                "username": cleaned_data["username"],
                "email": cleaned_data["email"],
                "password": cleaned_data["password"],
                "first_name": cleaned_data.get("first_name"),
                "last_name": cleaned_data.get("last_name"),
            }

            user_service = UserApplicationService(log=logger)
            user = user_service.register_user(user_data)
            if isinstance(user, str):
                # If the result is an error message (string), return it
                if "email" in user:
                    form.add_error("email", user)
                elif "username" in user:
                    form.add_error("username", user)
                return self.form_invalid(form)
            
     

            messages.success(self.request, "User Register Successfully !")

            return redirect(self.success_url)

        except ValidationError as e:

            return self.form_invalid(form)

        except Exception as e:

            return HttpResponseServerError(f"An error occurred: {str(e)}")

    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        return self.render_to_response({"form": form})


class LoginView(FormView):
    form_class = UserLoginForm
    template_name = "login.html"
    success_url = "product_page"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handles the valid form submission. Attempts to authenticate the user based on the provided
        username and password."""

        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        try:
            credentials = {"username": username, "password": password}
            user_service = UserApplicationService(log=logger)
            user = user_service.login_user(credentials, self.request)

            if user:
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "Invalid username or password.")
                return self.form_invalid(form)

        except ValidationError as e:
            # Handle validation errors and add to the form
            logger.error(f"Validation error: {str(e)}")  # Log the validation error
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handles the invalid form submission. Logs form errors and displays them to the user.
        # If the form is invalid, render the form with errors"""

        logger.warning(f"Form invalid: {form.errors}")

        for field, errors in form.errors.items():
            for error in errors:
                # Pass the error message dynamically based on the form field
                messages.error(self.request, f"{field.capitalize()}: {error}")

        return self.render_to_response({"form": form})




class ProductPageView(TemplateView):
    template_name = "product_page.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)




class ForgotPasswordView(FormView):
    template_name = "forgot_password.html"
    form_class = ForgotPasswordForm
    success_url = "verify_otp"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            user_service = UserApplicationService(log=logger)
            result = user_service.request_password_reset(email)

            if result["success"]:
                # Generate JWT token for the user with email and expiration time
                expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)  # 10 minutes expiration
                payload = {"email": email, "exp": expiration_time}
                token = jwt.encode(payload, "jinal123", algorithm="HS256")

                
      
                
                # Send OTP to the email and include the token
                user_service.generate_and_send_otp(self.request, email,token)
                self.request.session['reset_token'] = token
                logger.info(f"Token {token} for {email} stored in session.")
                messages.success(self.request, "OTP has been sent to your email.")
                logger.info(f"OTP requested for email: {email}")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, result["error_message"])
                logger.warning(f"Failed to request password reset for email {email}: {result['error_message']}")
                return self.form_invalid(form)

        except Exception as e:
            logger.error(f"An error occurred while processing password reset request for email {email}: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request. Please try again later.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Form invalid: {form.errors}")
        return self.render_to_response({"form": form})


class OTPVerificationView(FormView):
    template_name = "verify_otp.html"
    form_class = OTPVerificationForm
    success_url = "reset_password"

    # In OTPVerificationView dispatch method

    def dispatch(self, request, *args, **kwargs):
        token = request.session.get('reset_token')  # Fetch token from session
     
        if not token:
            messages.error(request, "You must generate an OTP to access this page.")
            return redirect("forgot_password")
        
        try:
            # Decode the JWT token to get the email
            payload = jwt.decode(token, "jinal123", algorithms=["HS256"])
            email = payload.get("email")
            if not email:
                messages.error(request, "Invalid token.")
                return redirect("forgot_password")
            self.request.email = email  # Store the email in the request object for use in form_valid()
            self.request.token = token  # Store the token for later use
        except jwt.ExpiredSignatureError:
            messages.error(request, "The link has expired. Please request a new OTP.")
            return redirect("forgot_password")
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token.")
            return redirect("forgot_password")
        
        return super().dispatch(request, *args, **kwargs)



    def form_valid(self, form):
        otp = form.cleaned_data["otp"]
        email = self.request.email  # Use the email from the decoded token
        token = self.request.token  # Use the token stored in the request

        user_service = UserApplicationService(log=logger)

        if user_service.verify_otp(self.request,email, token, otp):
            messages.success(self.request, "OTP Verified successfully!")
            logger.info(f"OTP verified successfully for email {email}")
            return redirect(self.get_success_url())
        else:
            attempts = user_service.increment_otp_attempts(self.request)
            remaining_attempts = 3 - attempts

            if remaining_attempts <= 0:
                next_attempt_time_seconds = user_service.set_next_attempt_time(self.request, attempts)
                return self.form_invalid(form, next_attempt_time_seconds=next_attempt_time_seconds, is_disabled=True)
            else:
                messages.error(self.request, f"Invalid OTP. You have {remaining_attempts} attempts remaining.")
                logger.warning(f"Invalid OTP for email {email}. Attempts left: {remaining_attempts}")
                return self.form_invalid(form)

    def form_invalid(self, form, next_attempt_time_seconds=None, is_disabled=False):
        remaining_message = None
        if next_attempt_time_seconds:
            remaining_message = f"You can attempt again in: {next_attempt_time_seconds} seconds"

        return self.render_to_response({
            "form": form,
            "is_disabled": is_disabled,
            "remaining_message": remaining_message,
            "next_attempt_time_seconds": next_attempt_time_seconds
        })


class ResetPasswordView(FormView):
    template_name = "reset_password.html"
    form_class = ResetPasswordForm
    success_url = "/login/"

    def dispatch(self, request, *args, **kwargs):
        token = request.session.get("reset_token") 
        if not token:
            messages.error(request, "generate otp and verify first !")
            return redirect("forgot_password")

        try:
      
            payload = jwt.decode(token, "jinal123", algorithms=["HS256"])
            email = payload.get("email")
            if not email:
                messages.error(request, "Invalid token.")
                return redirect("forgot_password")
            self.request.email = email  # Store the email in the request object for use in form_valid()
        except jwt.ExpiredSignatureError:
            messages.error(request, "The link has expired. Please request a new OTP.")
            return redirect("forgot_password")
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token.")
            return redirect("forgot_password")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        new_password = form.cleaned_data["new_password"]
        email = self.request.email  # Use the email from the decoded token

        try:
            if email:
                user_service = UserApplicationService(log=logger)
                user_service.reset_password(email, new_password)
                logger.info(f"Password reset successfully for email {email}")
                messages.success(self.request, "Password reset successfully.")
                self.request.session.flush()
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "An error occurred.")
                logger.error(f"Password reset failed for email {email}")
                return self.form_invalid(form)

        except Exception as e:
            logger.error(f"Error occurred while resetting password for email {email}: {str(e)}")
            messages.error(self.request, "An error occurred while resetting your password. Please try again later.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response({"form": form})
