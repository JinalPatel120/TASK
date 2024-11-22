from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from shopping_site.infrastructure.logger.models import logger
from shopping_site.application.order.services import OrderApplicationService
from django.contrib.auth.decorators import login_required
from django.views import View
from django.shortcuts import render
from shopping_site.application.order.services import OrderApplicationService
from django.contrib.auth.mixins import LoginRequiredMixin
from shopping_site.application.cart_item.services import CartService
# views.py
from django.shortcuts import render, redirect
from django.views import View
from .forms import CheckoutForm


class CheckoutView(View):
    def get(self, request):
        # Get user's cart items
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        
        if not cart_items:
            return redirect('cart')  # If cart is empty, redirect to the cart page

        # Calculate total price
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        
        form = CheckoutForm()

        return render(request, 'checkout.html', {
            'cart_items': cart_items,
            'total_price': total_price,
            'form': form
        })

    def post(self, request):
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            shipping_address = form.cleaned_data['shipping_address']
            order = OrderApplicationService.create_order(request.user, shipping_address)

            # Redirect to the order confirmation page
            return redirect('order_confirmation', order_id=order.id)
        
        # If form is invalid, show the checkout page again
        return render(request, 'checkout.html', {'form': form})
