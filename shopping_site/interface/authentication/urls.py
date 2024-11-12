# shopping_site/interface/authentication/urls.py

from django.urls import path
from .views import RegisterView,LoginView,ForgotPasswordView,ResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('forgot/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset/<str:email>/', ResetPasswordView.as_view(), name='reset_password'),

]
