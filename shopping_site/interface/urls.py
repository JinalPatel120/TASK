# shopping_site/interface/urls.py

from django.urls import path, include

urlpatterns = [
    path('', include('shopping_site.interface.authentication.urls')),

]
