# shopping_site/interface/cart_item/urls

from django.urls import path
from shopping_site.interface.cart_item.views import CartView,UpdateCartItemView,RemoveCartItemView

urlpatterns = [
     path('cart/', CartView.as_view(), name='cart_page'),
     path('cart/update/<uuid:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),  # Update cart item
    path('cart/remove/<uuid:item_id>/', RemoveCartItemView.as_view(), name='remove_cart_item'),  # Remove cart item
    
]
