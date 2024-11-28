from django.urls import path
from .views import (
    CheckoutView,
    OrderSummaryView,
    PlaceOrderView,
    EditAddressView,
    SetDefaultAddressView,
    UpdateAddressView,
    OrderConfirmationView,
    DownloadInvoiceView,
    RemoveAddressView,
    UserProfileView,
    CancelOrderView,
    TrackOrderView,
    ManageSession,
)

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("order/summary/", OrderSummaryView.as_view(), name="order_summary"),
    path("place-order/", PlaceOrderView.as_view(), name="place_order"),
    path("edit_address/", EditAddressView.as_view(), name="edit_address"),
    path("set_default_address/",SetDefaultAddressView.as_view(),name="set_default_address",),
    path("update_address", UpdateAddressView.as_view(), name="update_address"),
    path("order_confirmation/<int:order_id>/",OrderConfirmationView.as_view(),name="order_confirmation"),
    path("download_invoice/<int:order_id>/",DownloadInvoiceView.as_view(),name="download_invoice"),
    path("remove_address/<int:address_id>/",RemoveAddressView.as_view(),name="remove_address"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("track_order/<int:order_id>/", TrackOrderView.as_view(), name="track_order"),
    path("cancel_order/<int:order_id>/", CancelOrderView.as_view(), name="cancel_order"),
    path("manage_session/<str:session_id>/", ManageSession.as_view(),name="manage_session"),
    
]
