from django.shortcuts import redirect,render
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from .forms import RegistrationForm,UserLoginForm,ForgotPasswordForm,ResetPasswordForm,OTPVerificationForm
from shopping_site.application.authentication.services import UserApplicationService 
from django.contrib import messages
import logging
from django.views.generic import TemplateView

logger = logging.getLogger('shopping_site')

class RegisterView(FormView):
    """
    Class-based view to handle user registration.
    """
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = 'login'  # The URL to redirect after successful registration

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

            # Use the UserApplicationService to register a new user
            user = UserApplicationService.register_user(user_data)
            if isinstance(user, str):
                # If the result is an error message (string), return it
                if 'email' in user:
                    form.add_error('email', user)
                elif 'username' in user:
                    form.add_error('username', user)
                return self.form_invalid(form)
            # Log in the user after successful registration
            login(self.request, user)

            # Return success response (redirects to the home page)
            messages.success(self.request,'User Register Successfully !')
            logger.info(f"User registered and logged in: {cleaned_data['username']}")
            return redirect(self.success_url)

        except ValidationError as e:
            logger.error(f"Validation error during registration: {str(e)}")
            return self.form_invalid(form)

        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
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
   

    def form_valid(self, form):
        """
        Handles the valid form submission. Attempts to authenticate the user based on the provided
        username and password."""
         
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        logger.info(f"Login attempt with username: {username}")  

        try:
            credentials = {
                'username': username,
                'password': password
            }
            user = UserApplicationService.login_user(credentials,self.request)       
            if user:
                logger.info(f"Authentication successful for user: {username}")  
                login(self.request, user)
                return redirect(self.get_success_url())
            else:
                logger.warning(f"Authentication failed for username: {username}")  # Log failed authentication
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

class ForgotPasswordView(FormView):
    template_name = 'forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = 'verify_otp'

    def form_valid(self, form):
        """ 
        This view allows users to request a password reset by providing their email address.
        If the email is associated with a user, an OTP (One-Time Password) is generated and sent to that email.
        """

        email = form.cleaned_data['email']
        try:
            result = UserApplicationService.request_password_reset(email)

            if result["success"]:    # If successful, generate and send OTP, then redirect
                UserApplicationService.generate_and_send_otp(self.request, email)
                self.request.session['reset_email'] = email
                messages.success(self.request, "OTP has been sent to your email.")
                logger.info(f"OTP requested for email: {email}")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, result["error_message"])  # If user with this email does not exist, return error message
                logger.warning(f"Failed to request password reset for email {email}: {result['error_message']}")
                return self.form_invalid(form)
            
        except Exception as e:
            # Catch any unexpected errors and log them
            logger.error(f"An error occurred while processing password reset request for email {email}: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request. Please try again later.")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        """ 
        Handles invalid form submissions. Logs form errors and renders the form with error messages.
            
        """
        logger.warning(f"Form invalid: {form.errors}")
        return self.render_to_response({'form': form})


class OTPVerificationView(FormView):
    template_name = 'verify_otp.html'
    form_class = OTPVerificationForm
    success_url = 'reset_password'

    def dispatch(self, request, *args, **kwargs):
        # Check if OTP is verified before allowing access to the reset password page
        if not request.session.get('reset_email'):
            messages.error(request, "You must generate an OTP to access this page.")
            return redirect('forgot_password')
        return super().dispatch(request, *args, **kwargs)  

    def form_valid(self, form):
        """
        verified with OTP and if User entered OTP was verified than redirect to reset page
        
        """
        otp = form.cleaned_data['otp']
        email = self.request.session.get('reset_email')
        try:
            verify=UserApplicationService.verify_otp(self.request,email, otp)
            if email and verify:
                self.request.session['otp_verified'] = True
                messages.success(self.request, "OTP Verified successfully!")
                logger.info(f"OTP verified successfully for email {email}")
                return redirect(self.get_success_url())  
            else:
                messages.error(self.request, "Invalid OTP. Please try again.")
                logger.warning(f"Invalid OTP for email {email}")
                return redirect('verify_otp')
            
        except Exception as e:
            # Handle any unexpected errors during OTP verification
            logger.error(f"Error occurred during OTP verification for email {email}: {str(e)}")
            return self.form_invalid(form)
        
    def form_invalid(self, form):     
        """ 
        Handles invalid form submissions. Logs form errors and renders the form with error messages.
        """
        for field, errors in form.errors.items():
            for error in errors:
                # Pass the error message dynamically based on the form field
                messages.error(self.request, f"{field.capitalize()}: {error}")
        
        return self.render_to_response({'form': form})
  
class ProductPageView(TemplateView):
    template_name = 'product_page.html'


class ResetPasswordView(FormView):
    template_name = 'reset_password.html'
    form_class = ResetPasswordForm
    success_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # Check if OTP is verified before allowing access to the reset password page
        if not request.session.get('reset_email'):
            messages.error(request, "You must generate an OTP to access this page.")
            return redirect('forgot_password')

        # Check if OTP has been successfully verified (otp_verified in session)
        if not request.session.get('otp_verified', False):
            messages.error(request, "You need to verify the OTP first.")
            return redirect('verify_otp')  # Redirect to OTP verification page

        return super().dispatch(request, *args, **kwargs)  

    def form_valid(self, form):
        new_password = form.cleaned_data['new_password']
        email = self.request.session.get('reset_email')
        try:

            if email:
                UserApplicationService.reset_password(email, new_password)
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
        """ 
        Handles invalid form submissions. Logs form errors and renders the form with error messages.
        """
        return self.render_to_response({'form': form})

            