# shopping_site/interface/authentication/urls.py

from django.urls import path
from .views import RegisterView,LoginView,ForgotPasswordView,ResetPasswordView,OTPVerificationView,ForgotPasswordView,ResetPasswordView

urlpatterns = [
    path('', RegisterView.as_view(), name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('forgot/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset_password/', ResetPasswordView.as_view(), name='reset_password'),
    path('verify_otp/',OTPVerificationView.as_view(),name='verify_otp')


]
