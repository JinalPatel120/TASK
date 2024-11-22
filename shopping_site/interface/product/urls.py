# shopping_site/interface/product/urls

from django.urls import path
from .views import ProductListView, ProductDetailView, ProductSearchView, ProductCreateView, ProductUpdateView, ProductDeleteView
from shopping_site.interface.cart_item.views import AddToCartView,CartView,UpdateCartItemView,RemoveCartItemView,UpdateCartCountView

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<uuid:product_id>/', ProductDetailView.as_view(), name='product_detail'),
    path('search/', ProductSearchView.as_view(), name='product_search'),
    path('create/', ProductCreateView.as_view(), name='product_create'),
    path('update/<uuid:product_id>/', ProductUpdateView.as_view(), name='product_update'),
    path('delete/<uuid:product_id>/', ProductDeleteView.as_view(), name='product_delete'),
    path('add_to_cart/<uuid:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update_cart_count/', UpdateCartCountView.as_view(), name='update_cart_count'),
    path('cart/', CartView.as_view(), name='cart_page'),
    path('cart/update/<int:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),  # Update cart item
    path('cart/remove/<int:item_id>/', RemoveCartItemView.as_view(), name='remove_cart_item'), 
    
]
