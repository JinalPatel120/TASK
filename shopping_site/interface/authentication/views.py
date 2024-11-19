from django.shortcuts import redirect,render
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError,HttpResponseRedirect
from .forms import RegistrationForm,UserLoginForm,ForgotPasswordForm,ResetPasswordForm,OTPVerificationForm
from shopping_site.application.authentication.services import UserApplicationService 
from django.contrib import messages
from django.views.generic import TemplateView
from shopping_site.infrastructure.logger.models import logger
from datetime import datetime,timedelta

import jwt


class RegisterView(FormView):
    """
    Class-based view to handle user registration.
    """
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = 'login'  # The URL to redirect after successful registration
    user_service = UserApplicationService(log=logger)

    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
           # Get cleaned data from form
            cleaned_data = form.cleaned_data
         
            user_data = {
                "username": cleaned_data['username'],
                "email": cleaned_data['email'],
                "password": cleaned_data['password'],
                "first_name": cleaned_data.get('first_name'),
                "last_name": cleaned_data.get('last_name')
            }

            
            user = self.user_service.register_user(user_data)
            if isinstance(user, str):
                # If the result is an error message (string), return it
                if 'email' in user:
                    form.add_error('email', user)
                elif 'username' in user:
                    form.add_error('username', user)
                return self.form_invalid(form)
            messages.success(self.request,'User Register Successfully !')
         
            return redirect(self.success_url)

        except ValidationError as e:
       
            return self.form_invalid(form)

        except Exception as e:
        
            return HttpResponseServerError(f"An error occurred: {str(e)}")

    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        return self.render_to_response({'form': form})   

class LoginView(FormView):
    form_class = UserLoginForm
    template_name = 'login.html'
    success_url='product_page'
    user_service = UserApplicationService(log=logger)
   
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handles the valid form submission. Attempts to authenticate the user based on the provided
        username and password."""

        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
       

        try:
            credentials = {
                'username': username,
                'password': password
            }
            
            user = self.user_service.login_user(credentials,self.request)
               
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
        # If the form is invalid, render the form with errors """

        logger.warning(f"Form invalid: {form.errors}")

        for field, errors in form.errors.items():
            for error in errors:
                # Pass the error message dynamically based on the form field
                messages.error(self.request, f"{field.capitalize()}: {error}")
        
        return self.render_to_response({'form': form})

class ProductPageView(TemplateView):
    template_name = 'product_page.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('login')  
        return super().dispatch(request, *args, **kwargs)
           

class ForgotPasswordView(FormView):
    """
    View to handle the forgot password process. It generates and sends an OTP to the provided email address.
    Once the email is submitted, an OTP is sent to the user to verify their identity.
    """

    template_name = "forgot_password.html"
    form_class = ForgotPasswordForm
    success_url = "verify_otp"
    user_service = UserApplicationService(log=logger)

    def form_valid(self, form):
        """
        Handles the successful submission of the forgot password form. This method generates a token for the email,
        sends an OTP to the user's email address, and then redirects the user to the OTP verification page.
        """
        email = form.cleaned_data["email"]
        try:
            
            
            # Generate token using the UserApplicationService
            token = self.user_service.generate_token(email=email)
            
            # Send OTP to the email with the token
            self.user_service.generate_and_send_otp(email=email, token=token)
            messages.success(self.request, "OTP has been sent to your email. Please check your inbox.")
            return redirect("forgot_password")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request.")
            return self.form_invalid(form)


class OTPVerificationView(FormView):
    """
    View to handle OTP verification. It validates the OTP entered by the user and redirects them to the reset password page
    if the OTP is correct.
    """
    template_name = "verify_otp.html"
    form_class = OTPVerificationForm
    success_url = "reset_password"
    user_service = UserApplicationService(log=logger)

    def dispatch(self, request, *args, **kwargs):
        """
        Handles the initial request for OTP verification. It extracts the token from the URL and decodes it to verify its validity.
        """
        token = request.GET.get('token')
        
        # Ensure the token is provided in the URL
        if not token:
            messages.error(request, "Invalid or missing token. Please request a new OTP.")
            return redirect("forgot_password")

        try:
         
            payload, error_message = self.user_service.decode_token(token=token)
            
            if not payload:
                messages.error(request, error_message)
                return redirect("forgot_password")
            
            email = payload.get("email")
            if not email:
                messages.error(request, "Invalid token.")
                return redirect("forgot_password")
            
            self.request.email = email
            self.request.token = token
        except jwt.ExpiredSignatureError:
            messages.error(request, "The link has expired. Please request a new OTP.")
            return redirect("forgot_password")
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token.")
            return redirect("forgot_password")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handles the successful submission of the OTP verification form. Verifies the OTP entered by the user and, if correct,
        redirects them to the reset password page with the token.
        """
        otp = form.cleaned_data["otp"]
        email = self.request.email
        token = self.request.token

        

        # Verify OTP
        result = self.user_service.verify_otp(email=email, otp=otp, token=token)
        if result["success"]:
            messages.success(self.request, result["message"])
            return redirect(f"/reset_password/?token={token}") 
        else:
            messages.error(self.request, result["message"])
            return self.form_invalid(form)
        
    def get(self, request, *args, **kwargs):
        if 'resend' in request.GET:
            return self.resend_otp(request)
        return super().get(request, *args, **kwargs)


    def resend_otp(self, request):
       
        token = request.GET.get('token', None)  
        if not token:
            messages.error(request, "No token found. Please try again.")
            return redirect('verify_otp')  
        email = self.user_service.get_email_from_token(token=token) 

        if email:          
            otp = self.user_service.generate_and_send_otp(email=email, token=token,resend=True)  
            if otp:
                messages.success(request, "A new OTP has been sent to your email.")
            else:
                messages.error(request, "Failed to resend OTP. Please try again.")
        else:
            messages.error(request, "Invalid or expired token.")
        
        return redirect(f"/verify_otp/?token={token}")
        
        
class ResetPasswordView(FormView):
    """
    View to handle the password reset process. After verifying the OTP, the user can reset their password here.
    """

    template_name = "reset_password.html"
    form_class = ResetPasswordForm
    success_url = "/login/"
    user_service = UserApplicationService(log=logger)

    def dispatch(self, request, *args, **kwargs):
        """
        Handles the initial request for resetting the password. It extracts the token from the URL, validates it,
        and checks if the email associated with the token exists.
        """
        token = request.GET.get('token')

        # If token is not found in GET parameters, redirect to the forgot password page with an error
        if not token:
            messages.error(request, "Invalid or missing token. Please generate OTP first.")
            return redirect("forgot_password")

        try:
          
            payload, error_message = self.user_service.decode_token(token=token)

            if not payload:
                messages.error(request, error_message)
                return redirect("forgot_password")  # Redirect to forgot password view if token is invalid

            email = payload.get("email")
            if not email:
                messages.error(request, "Invalid token.")
                return redirect("forgot_password")  # Redirect to forgot password view if email is missing in the payload

            self.request.email = email  # Save email from token to request for later use

        except jwt.ExpiredSignatureError:
            messages.error(request, "The link has expired. Please request a new OTP.")
            return redirect("forgot_password")  # Redirect to forgot password view if the token is expired
        except jwt.InvalidTokenError:
            messages.error(request, "Invalid token.")
            return redirect("forgot_password")  # Redirect to forgot password view if the token is invalid

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handles the successful submission of the reset password form. It resets the user's password and redirects them to the login page.
        """
        new_password = form.cleaned_data["new_password"]
        email = self.request.email  # Get the email from the decoded token

        try:
            if email:    
                self.user_service.reset_password(email=email, new_password=new_password)
                logger.info(f"Password reset successfully for email {email}")
                messages.success(self.request, "Password reset successfully.")
                return redirect(self.get_success_url())  # Redirect to the login page
            messages.error(self.request, "An error occurred.")
            logger.error(f"Password reset failed for email {email}")
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error occurred while resetting password for email {email}: {str(e)}")
            messages.error(self.request, "An error occurred while resetting your password. Please try again later.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Handles invalid form submissions. This method is called when the form is not valid.
        """
        return self.render_to_response({"form": form})
