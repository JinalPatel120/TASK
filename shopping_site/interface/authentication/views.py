from django.shortcuts import redirect, render,HttpResponse
from django.contrib.auth import login
from django.views.generic.edit import CreateView,FormView
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from .forms import RegistrationForm,UserLoginForm,ForgotPasswordForm,ResetPasswordForm,OTPVerificationForm
from shopping_site.application.authentication.services import UserApplicationService 
from django.contrib import messages
import logging


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
    
        return self.render_to_response({'form': form})   # If form is invalid, render the form again with errors



class LoginView(FormView):
    form_class = UserLoginForm
    template_name = 'login.html'
    success_url = 'register'

    def form_valid(self, form):
        # Get the cleaned data from the form
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
                return redirect(self.success_url)  
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
        # If the form is invalid, render the form with errors
        logger.warning(f"Form invalid: {form.errors}")
        return self.render_to_response({'form': form})
        

class ForgotPasswordView(FormView):
    template_name = 'forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = 'verify_otp'

    def form_valid(self, form):
        email = form.cleaned_data['email']
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


class OTPVerificationView(FormView):
    template_name = 'verify_otp.html'
    form_class = OTPVerificationForm
    success_url = 'reset_password'

    def form_valid(self, form):
        otp = form.cleaned_data['otp']
        email = self.request.session.get('reset_email')
        verify=UserApplicationService.verify_otp(self.request,email, otp)
        if email and verify:
            messages.success(self.request, "OTP Verified successfully!")
            logger.info(f"OTP verified successfully for email {email}")
            return redirect(self.get_success_url())  
        else:
            messages.error(self.request, "Invalid OTP. Please try again.")
            logger.warning(f"Invalid OTP for email {email}")
            return redirect('verify_otp')
        
    def form_invalid(self, form):     # Optional: Handle form invalid case if needed
        messages.error(self.request, "OTP must be in digits")
        return self.render_to_response({'form': form})
            

class ResetPasswordView(FormView):
    template_name = 'reset_password.html'
    form_class = ResetPasswordForm
    success_url = '/login/'

    def form_valid(self, form):
        new_password = form.cleaned_data['new_password']
        email = self.request.session.get('reset_email')
        if email:
            UserApplicationService.reset_password(email, new_password)
            logger.info(f"Password reset successfully for email {email}")
            messages.success(self.request, "Password reset successfully.")
            return redirect(self.get_success_url()) 
        else:
            messages.error(self.request, "An error occurred.")
            logger.error(f"Password reset failed for email {email}")
            return self.form_invalid(form)