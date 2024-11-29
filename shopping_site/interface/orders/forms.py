# forms.py
from django import forms
from shopping_site.domain.authentication.models import User,UserAddress

class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(max_length=255, required=True)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'gender', 'profile_picture']

class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['full_name', 'mobile_number', 'flat_building', 'area', 'landmark', 'pincode', 'city', 'state', 'address_type']


class ChangePasswordForm(forms.Form):
    old_password=forms.CharField(label='Old Password', widget=forms.PasswordInput)
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
