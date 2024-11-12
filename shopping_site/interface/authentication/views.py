from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from .forms import RegistrationForm,UserLoginForm
from shopping_site.application.authentication.services import UserApplicationService ,PasswordResetService # Assuming the service is correctly imported
from django.views import View
from django.contrib import messages
from django.http import JsonResponse

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

            # Prepare user data
            user_data = {
                "username": cleaned_data['username'],
                "email": cleaned_data['email'],
                "password": cleaned_data['password'],
                "first_name": cleaned_data.get('first_name', ''),
                "last_name": cleaned_data.get('last_name', '')
            }

            # Use the UserApplicationService to register a new user
            user = UserApplicationService.register_user(user_data)

            # Log in the user after successful registration
            login(self.request, user)

            # Return success response (redirects to the home page)
            return redirect(self.success_url)

        except ValidationError as e:
      
            return self.form_invalid(form)

        except Exception as e:
            # Handle any other exceptions
            return HttpResponseServerError(f"An error occurred: {str(e)}")

    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        # If form is invalid, render the form again with errors
        return self.render_to_response({'form': form})


class LoginView(View):
    """User login view"""

    def get(self, request):
        # Render the login form on GET request
        form = UserLoginForm()
        return render(request, "login.html", {"form": form})

   
    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = UserApplicationService.login_user(username,password)
          
            if user is not None:
              
                return redirect('product_page')  # Redirect to product page
            else:
                messages.error(request, "Invalid username or password.")
                return render(request, 'login.html', {'form': form})

        else:
            messages.error(request, "There was an error with your login credentials.")
            return render(request, 'login.html', {'form': form})
        




class ForgotPasswordView(View):
    """
    This view handles forgot password requests.
    """

    def get(self, request):
        """
        Displays the form to enter the email for password reset.
        """
        return render(request, 'forgot_password.html')

    def post(self, request):
        """
        Handles the email submission for the password reset.
        """
        email = request.POST.get("email")
        # Request password reset using the PasswordResetService
        result = PasswordResetService.request_password_reset(email)
       

        if result :
            return redirect('reset_password', email=email)
        else:
          return render(request,'forgot_password.html')


class ResetPasswordView(View):
    """
    This view handles the reset password functionality.
    """

    def get(self, request, email):
        """
        Displays the form to enter the new password and confirm it.
        """
        return render(request, 'reset_password.html', {'email': email})

    def post(self, request, email):
        """
        Handles the new password and confirmation submission for reset.
        """
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        
        # Reset the password using PasswordResetService
        result = PasswordResetService.reset_password(email, new_password, confirm_password)

        if result:
            return redirect('login')  # Redirect to login page
        else:
            return JsonResponse({
                "status": "error",
                "message": result
            }, status=400)
