from django.urls import path
from . import views

urlpatterns = [
    # Other URLs...
    path('checkout/', views.checkout_view, name='checkout'),
    path('order_summary/<str:order_id>/', views.order_summary_view, name='order_summary'),
]
