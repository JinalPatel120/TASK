from django.shortcuts import render, redirect
from django.views import View
from shopping_site.application.cart_item.services import CartService
from shopping_site.application.order.services import OrderApplicationService
from shopping_site.application.authentication.services import UserApplicationService
from shopping_site.infrastructure.logger.models import logger
from django.contrib import messages
from shopping_site.interface.authentication.forms import UserAddressForm



class CheckoutView(View):
    cart_service = CartService(log=logger)
    user_service = UserApplicationService(log=logger)

    def get(self, request):
        try:
            # Retrieve cart items
            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect('cart_page')

            # Get user details for name display
            user_first_name, user_last_name = self.cart_service.get_user_details_by_username(request.user.username)

            # Calculate total price
            total = sum(item.total_price for item in cart_items)

            # Retrieve saved address (if any) and default address logic
            saved_address = self.user_service.get_user_address(request.user)
            default_address = self.user_service.get_default_address(request.user)  # Assuming a method to get default address

            # Initialize form with saved address data if present
            initial_data = {}
            if saved_address:
                initial_data = {
                    'flat_building': saved_address.get('flat_building', ''),
                    'city': saved_address.get('city', ''),
                    'pincode': saved_address.get('pincode', '')
                }

            form = UserAddressForm(initial=initial_data)

            # Render checkout page with the address details
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'user_first_name': user_first_name,
                'user_last_name': user_last_name,
                'form': form,
                'saved_address': saved_address,
                'default_address': default_address  # Add default address to context
            })

        except Exception as e:
            logger.error(f"Error during checkout: {str(e)}")
            messages.error(request, "An error occurred during checkout.")
            return redirect('cart_page')

    def post(self, request):
        try:
            # Handle address form submission
            form = UserAddressForm(request.POST)
            if form.is_valid():
                # Get cleaned data from form
                shipping_address_data = form.cleaned_data

                # Create or update the user's address
                address = self.user_service.get_or_create_address(request.user, shipping_address_data)

                # Optionally, save the address to session
                request.session['shipping_address'] = {
                    'flat_building': address.flat_building,
                    'city': address.city,
                    'pincode': address.pincode
                }

                # Redirect to order summary page
                return redirect('order_summary')

            # If form is invalid, re-render checkout page with form errors
            cart_items = self.cart_service.get_cart_items(request.user, request)
            total = sum(item.total_price for item in cart_items)
            messages.error(request, "There was an error with your shipping address.")
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'form': form
            })

        except Exception as e:
            logger.error(f"Error handling address: {str(e)}")
            messages.error(request, "An error occurred while processing the address.")
            return redirect('checkout')


class OrderSummaryView(View):
    cart_service = CartService(log=logger)

    def get(self, request):
        try:
            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect('cart_page')

            total = sum(item.total_price for item in cart_items)
            shipping_address = request.session.get('shipping_address', None)

            if not shipping_address:
                messages.error(request, "No shipping address found.")
                return redirect('checkout')

            print('shipping address',shipping_address)
            return render(request, 'order_summary.html', {
                'cart_items': cart_items,
                'total': total,
                'shipping_address': shipping_address
            })
        except Exception as e:
            logger.error(f"Error displaying order summary: {str(e)}")
            messages.error(request, "An error occurred while displaying the order summary.")
            return redirect('cart_page')



class PlaceOrderView(View):
    user_service = UserApplicationService(log=logger)

    def post(self, request):
        try:
            if request.user.is_authenticated:
                # Retrieve the shipping address (assumed to be saved earlier)
                # Either from session or directly from database.
                address = request.session.get('shipping_address', None)

                if not address:
                    messages.error(request, "No shipping address found. Please provide an address.")
                    return redirect('checkout')

                # Create the order with the retrieved address
                order = OrderApplicationService.create_order(request.user, address)

                # If order creation was successful
                messages.success(request, "Your order has been placed successfully!")
                return redirect('order_summary')

            else:
                messages.error(request, "You need to be logged in to place an order.")
                return redirect('login')

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            messages.error(request, "An error occurred while placing your order.")
            return redirect('checkout')






class EditAddressView(View):
    def get(self, request):
        try:
            # Retrieve the current address for the user
            saved_address = user_service.get_user_address(request.user)
            
            # Initialize the form with the current address data
            form = UserAddressForm(instance=saved_address)
            
            return render(request, 'edit_address.html', {'form': form})

        except Exception as e:
            messages.error(request, "Error while loading the address form.")
            return redirect('checkout')

    def post(self, request):
        try:
            # Retrieve the current address for the user
            saved_address = user_service.get_user_address(request.user)
            
            # Populate the form with POST data and the current address instance
            form = UserAddressForm(request.POST, instance=saved_address)
            
            if form.is_valid():
                # Save the updated address
                form.save()
                messages.success(request, "Address updated successfully.")
                return redirect('order_summary')  # Redirect to order summary page
            else:
                messages.error(request, "Please correct the errors below.")
                
            return render(request, 'edit_address.html', {'form': form})

        except Exception as e:
            messages.error(request, "Error while updating the address.")
            return redirect('checkout')


user_service = UserApplicationService(log=logger)

class SetDefaultAddressView(View):
    def post(self, request):
        try:
            # Get the user's current address
            address = user_service.get_user_address(request.user)

            # Set the retrieved address as the default
            user_service.set_default_address(request.user, address)
            
            messages.success(request, "Address has been set as default.")
            return redirect('order_summary')

        except Exception as e:
            messages.error(request, "Error setting default address.")
            return redirect('checkout')
