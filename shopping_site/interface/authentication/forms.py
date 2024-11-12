
from django import forms
from django.core.exceptions import ValidationError
import re

class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        required=True,
        error_messages={'required': 'Username is required.'}
    )
    email = forms.EmailField(
        required=True,
        error_messages={'required': 'Email is required.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput, 
        required=True,
        error_messages={'required': 'Password is required.'}
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, 
        required=True,
        error_messages={'required': 'Confirm password is required.'}
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        error_messages={'required': 'First Name is Required'}
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        error_messages={'required': 'last Name is required.'}
    )


    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Basic email pattern check
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format.")
        


    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password
    
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password != confirm_password:
            raise ValidationError("Password and Confirm Password do not match.")
        
        return cleaned_data

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)
    
   
