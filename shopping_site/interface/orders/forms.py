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

