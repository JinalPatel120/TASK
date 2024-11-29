# shopping_site/interface/cart_item/urls

from django.urls import path
from .views import ( AddToCartView,
                    UpdateCartCountView,
                      CartView,
                      UpdateCartItemView,
                      RemoveCartItemView
                      )

urlpatterns = [
    path('add_to_cart/<uuid:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update_cart_count/', UpdateCartCountView.as_view(), name='update_cart_count'),
    path('cart/', CartView.as_view(), name='cart_page'),
    path('cart/update/<int:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),  
    path('cart/remove/<int:item_id>/', RemoveCartItemView.as_view(), name='remove_cart_item'), 
    
]
