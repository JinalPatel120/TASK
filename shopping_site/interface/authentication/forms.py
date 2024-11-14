from django import forms
from django.core.exceptions import ValidationError
from shopping_site.domain.authentication.models import User
import re

class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True,
        error_messages={'required': 'Confirm password is required.'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
        error_messages = {
            'username': {'required': 'Username is required.'},
            'email': {'required': 'Email is required.'},
            'first_name': {'required': 'First Name is required.'},
            'last_name': {'required': 'Last Name is required.'},
            'password': {'required': 'Password is required.'},
         
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 8:
            raise ValidationError("username must be at least 8 characters long.")
        if not re.search(r'\d', username):
            raise ValidationError("username must contain at least one digit.")
        if not re.search(r'[A-Za-z]', username):
            raise ValidationError("username must contain at least one letter.")
        return username
    

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password must contain at least one letter.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
   
        if password != confirm_password:
            self.add_error('confirm_password', 'Password and Confirm Password do not match.')
        
        return cleaned_data

class UserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
        required=False,
        error_messages={'required': 'Please enter your username.'} 
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
        required=False,
        error_messages={'required': 'Please enter your password.'}  
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if not username:
            self.add_error('username', 'Username is required.')
        if not password:
            self.add_error('password', 'Password is required.')

        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.CharField(label='Email',required=False,
        error_messages={'required': 'Please enter your email ID.'} )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('This field is required.')

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError('Enter a valid email address.')
        return email


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(label='OTP', max_length=6,required=False,  error_messages={
            'required': 'Please enter the OTP to proceed.'  
        })

    if not otp:
        raise ValidationError('This field is required.')
    
    def clean_otp(self):
        otp = self.cleaned_data.get('otp')

        if not otp:
            raise ValidationError('This field is required.')
    
        if not otp.isdigit():
            raise forms.ValidationError("OTP must be in digits.")
        
        if len(otp) != 6:
            raise forms.ValidationError("OTP must be exactly 6 digits long.")

        return otp
    

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
    

