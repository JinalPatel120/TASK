# shopping_site/interface/product/urls

from django.urls import path
from .views import ProductListView, ProductDetailView, ProductSearchView, ProductCreateView, ProductUpdateView, ProductDeleteView,ProductManageView
from shopping_site.interface.cart_item.views import AddToCartView,CartView,UpdateCartItemView,RemoveCartItemView,UpdateCartCountView
from shopping_site.interface.orders.views import RemoveAddressView,CheckoutView,OrderSummaryView,PlaceOrderView,EditAddressView,OrderConfirmationView,SetDefaultAddressView,UpdateAddressView,DownloadInvoiceView,UserProfileView,TrackOrderView

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<uuid:product_id>/', ProductDetailView.as_view(), name='product_detail'),
    path('search/', ProductSearchView.as_view(), name='product_search'),
    path('create/', ProductCreateView.as_view(), name='product_create'),
    path('product/manage/',ProductManageView.as_view(),name='product_manage'),
    path('update/<uuid:product_id>/', ProductUpdateView.as_view(), name='product_update'),
    path('delete/<uuid:product_id>/', ProductDeleteView.as_view(), name='product_delete'),
    path('add_to_cart/<uuid:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update_cart_count/', UpdateCartCountView.as_view(), name='update_cart_count'),
    path('cart/', CartView.as_view(), name='cart_page'),
    path('cart/update/<int:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),  
    path('cart/remove/<int:item_id>/', RemoveCartItemView.as_view(), name='remove_cart_item'), 
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order/summary/', OrderSummaryView.as_view(), name='order_summary'),
    path('place-order/', PlaceOrderView.as_view(), name='place_order'),
    path('edit_address/', EditAddressView.as_view(), name='edit_address'),
    path('set_default_address/', SetDefaultAddressView.as_view(), name='set_default_address'),
    path('api/update_address', UpdateAddressView.as_view(), name='update_address'),
    path('order_confirmation/<int:order_id>/', OrderConfirmationView.as_view(), name='order_confirmation'),
    path('download_invoice/<int:order_id>/', DownloadInvoiceView.as_view(), name='download_invoice'),
    path('api/remove_address/<int:address_id>/', RemoveAddressView.as_view(), name='remove_address'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('track_order/<int:order_id>/', TrackOrderView.as_view(), name='track_order'),

]
