# shopping_site/interface/urls.py

from django.urls import path, include

urlpatterns = [
    path('auth/', include('shopping_site.interface.authentication.urls')),
    path('', include('shopping_site.interface.product.urls')),
    path('cart/',include('shopping_site.interface.cart_item.urls')),
    path('orders/',include('shopping_site.interface.orders.urls'))

]
