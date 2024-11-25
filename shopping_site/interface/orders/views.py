from django.shortcuts import render, redirect
from django.views import View
from shopping_site.application.cart_item.services import CartService
from shopping_site.application.order.services import OrderApplicationService
from shopping_site.application.authentication.services import UserApplicationService
from shopping_site.infrastructure.logger.models import logger
from django.contrib import messages
from shopping_site.interface.authentication.forms import UserAddressForm
from django.http import HttpResponse
from django.views import View
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import JsonResponse
from django.views import View
import json
from django.views.generic import TemplateView


class CheckoutView(View):
    cart_service = CartService(log=logger)
    user_service = UserApplicationService(log=logger)

    def get(self, request):
        try:
            # Retrieve cart items
            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect("cart_page")

            # Get user details for name display
            user_first_name, user_last_name = (
                self.cart_service.get_user_details_by_username(request.user.username)
            )

            # Calculate total price
            total = sum(item.total_price for item in cart_items)

            # Retrieve saved address (if any) and default address logic
            saved_address = self.user_service.get_user_address(request.user)
            default_address = self.user_service.get_default_address(request.user)
            # if saved_address:
            #     return redirect('order_summary')

            # Initialize form with saved address data if present
            initial_data = {}
            if saved_address:
                initial_data = {
                    "flat_building": saved_address.get("flat_building", ""),
                    "city": saved_address.get("city", ""),
                    "pincode": saved_address.get("pincode", ""),
                }

            form = UserAddressForm(initial=initial_data)

            # Render checkout page with the address details
            return render(
                request,
                "checkout.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "user_first_name": user_first_name,
                    "user_last_name": user_last_name,
                    "form": form,
                    "saved_address": saved_address,
                    "default_address": default_address,  # Add default address to context
                },
            )

        except Exception as e:
            logger.error(f"Error during checkout: {str(e)}")
            messages.error(request, "An error occurred during checkout.")
            return redirect("cart_page")

    def post(self, request):
        try:
            # Handle address form submission
            form = UserAddressForm(request.POST)
            if form.is_valid():
                # Get cleaned data from form
                shipping_address_data = form.cleaned_data

                # Create or update the user's address
                address = self.user_service.get_or_create_address(
                    request.user, shipping_address_data
                )

                # Optionally, save the address to session
                request.session["shipping_address"] = {
                    "flat_building": address.flat_building,
                    "city": address.city,
                    "pincode": address.pincode,
                }

                # Redirect to order summary page
                return redirect("order_summary")

            # If form is invalid, re-render checkout page with form errors
            cart_items = self.cart_service.get_cart_items(request.user, request)
            total = sum(item.total_price for item in cart_items)
            messages.error(request, "There was an error with your shipping address.")
            return render(
                request,
                "checkout.html",
                {"cart_items": cart_items, "total": total, "form": form},
            )

        except Exception as e:
            logger.error(f"Error handling address: {str(e)}")
            messages.error(request, "An error occurred while processing the address.")
            return redirect("checkout")



class OrderSummaryView(View):
    cart_service = CartService(log=logger)
    user_service = UserApplicationService(log=logger)
    order_service = OrderApplicationService()

    def get(self, request):
        try:
            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                return redirect("cart_page")

            total = sum(item.total_price for item in cart_items)
            addresses = self.user_service.get_user_addresses(request.user)

            shipping_address = request.session.get("shipping_address", None)

            if not shipping_address:
                messages.error(request, "No shipping address found.")
                return redirect("checkout")

            # # Assuming 'order_id' is needed here
            # order_id = None
       
            # order = self.order_service.create_order(request.user)
            # if order:
            #     order_id = order.id
            # else:
            #     messages.error(request, "An error occurred while creating the order.")
            #     return redirect("checkout")

            return render(
                request,
                "order_summary.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "shipping_address": shipping_address,
                    "addresses": addresses,
                    # "order_id": order_id,  # Pass the order_id to the template
                },
            )
        except Exception as e:
            logger.error(f"Error displaying order summary: {str(e)}")
            messages.error(
                request, "An error occurred while displaying the order summary."
            )
            return redirect("cart_page")


class PlaceOrderView(View):
    user_service = UserApplicationService(log=logger)
    order_service = OrderApplicationService()

    def post(self, request):

        try:
            if request.user.is_authenticated:
                # Retrieve the shipping address from the form data
                shipping_address_id = request.POST.get("shipping_address")

                if not shipping_address_id:
                    messages.error(
                        request,
                        "No shipping address selected. Please select one before placing your order.",
                    )
                    return redirect("order_summary")  # Redirect back to order summary

                # Fetch the address details using the ID
                address = self.user_service.get_address_by_id(
                    request.user, shipping_address_id
                )

                if not address:
                    messages.error(request, "Invalid shipping address.")
                    return redirect("order_summary")

                order = self.order_service.create_order(request.user, address)
                if order:
                    self.order_service.empty_cart(request.user)
                    messages.success(
                        request, "Your order has been placed successfully!"
                    )
                    return redirect("order_confirmation", order_id=order.id)
                # If order creation was successful
                messages.success(request, "Your order has been placed successfully!")
                return redirect(
                    "order_summary"
                )  # Or you can redirect to an order confirmation page

            else:
                messages.error(request, "You need to be logged in to place an order.")
                return redirect("login")

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            messages.error(request, "An error occurred while placing your order.")
            return redirect("checkout")


class EditAddressView(View):
    user_service = UserApplicationService(log=logger)

    def get(self, request):
        try:
            address_id = request.GET.get("address_id")
            if not address_id:
                messages.error(request, "Invalid address ID.")
                return redirect("checkout")

            # Retrieve the address to edit
            address = self.user_service.get_address_by_id(request.user, address_id)
            if not address:
                messages.error(request, "Address not found.")
                return redirect("checkout")

            # Initialize the form with the current address data
            form = UserAddressForm(instance=address)
            return render(request, "edit_address.html", {"form": form})

        except Exception as e:
            messages.error(request, "Error while loading the address form.")
            return redirect("checkout")

    def post(self, request):
        try:
            address_id = request.GET.get("address_id")
            address = self.user_service.get_address_by_id(request.user, address_id)

            # Populate the form with POST data and the current address instance
            form = UserAddressForm(request.POST, instance=address)

            if form.is_valid():
                # Save the updated address
                form.save()
                messages.success(request, "Address updated successfully.")
                return redirect("order_summary")  # Redirect to order summary page
            else:
                messages.error(request, "Please correct the errors below.")

            return render(request, "edit_address.html", {"form": form})

        except Exception as e:
            messages.error(request, "Error while updating the address.")
            return redirect("checkout")


class SetDefaultAddressView(View):
    user_service = UserApplicationService(log=logger)

    def post(self, request):
        try:
            # Get the user's current address
            address = self.user_service.get_user_address(request.user)

            # Set the retrieved address as the default
            self.user_service.set_default_address(request.user, address)

            messages.success(request, "Address has been set as default.")
            return redirect("order_summary")

        except Exception as e:
            messages.error(request, "Error setting default address.")
            return redirect("checkout")


class UpdateAddressView(View):
    def post(self, request, *args, **kwargs):
        # Parse the JSON body of the request
        data = json.loads(request.body)
        address_id = data.get("id")
        flat_building = data.get("flat_building")
        city = data.get("city")
        pincode = data.get("pincode")

        try:
            # Assuming `UserApplicationService` handles user-specific logic
            user_service = UserApplicationService(
                log=logger
            )  # Ensure `logger` is defined in your view or globally
            address = user_service.get_address_by_id(
                request.user, address_id
            )  # Get address using service
            address.flat_building = flat_building
            address.city = city
            address.pincode = pincode
            address.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "message": "Address not found"})


class OrderConfirmationView(TemplateView):
    template_name = "order_confirmation.html"
    order_service = OrderApplicationService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get("order_id")

        if not order_id:
            raise ValueError("Order ID is required to render this page.")

        order = self.order_service.get_order_by_id(order_id)
        if not order:
            return redirect("error_page")  # Assuming you have an error page

        context["order_id"] = order_id
        context["order"] = order
        return context



class DownloadInvoiceView(View):
    order_service = OrderApplicationService()

    def get(self, request, order_id):
        # Get the order details
        order = self.order_service.get_order_by_id(order_id)
        
        if not order:
            return HttpResponse("Order not found.", status=404)

        # If the total_amount isn't calculated yet, calculate it
        if order.total_amount is None:
            order.calculate_total_amount()

        # Create a response object with PDF content type
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="invoice_{order_id}.pdf"'
        )

        # Generate PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Draw the invoice content
        p.drawString(100, 750, f"Invoice for Order #{order.id}")
        p.drawString(
            100, 725, f"Customer: {order.user.first_name} {order.user.last_name}"
        )

        # Check if shipping_address is an object or string
        if isinstance(order, str):  # If it's a string, use it directly
            p.drawString(100, 700, f"Address: {order}")
        else:  # If it's an object, access its attributes
            p.drawString(
                100,
                700,
                f"Address: {order}, {order}, {order}",
            )

        p.drawString(100, 675, "Items:")


        order_items = self.order_service.invoice_items(order=order)
        y = 650
        for item in order_items:
            p.drawString(
                100, y, f"{item.product} - {item.quantity} x ${item.price}"
            )
            y -= 25

        # Draw the total amount
        p.drawString(100, y, f"Total: ${order.total_amount}")

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)

        return response



from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class RemoveAddressView(View):
    """
    CBV to handle the removal of an address.
    """

    def post(self, request, address_id):
        """
        Handles the request to remove an address by its ID.

        Args:
            request: The HTTP request object.
            address_id: The ID of the address to remove.

        Returns:
            JsonResponse: A JSON response indicating success or failure.
        """
        address_service = UserApplicationService(log=logger)
        success = address_service.remove_address(address_id)

        if success:
            return JsonResponse({'success': True}, status=200)
        else:
            return JsonResponse({'success': False, 'message': 'Address not found'}, status=404)
