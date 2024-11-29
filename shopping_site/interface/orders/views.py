from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from shopping_site.application.cart_item.services import CartService
from shopping_site.application.order.services import OrderApplicationService
from shopping_site.application.authentication.services import UserApplicationService
from shopping_site.domain.cart_item.models import Cart, CartItem
from shopping_site.infrastructure.logger.models import logger
from django.contrib import messages
from shopping_site.interface.authentication.forms import UserAddressForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import JsonResponse
import json
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from functools import wraps
from urllib.parse import parse_qs
from django.contrib.auth import update_session_auth_hash

class ManageSession(View):
    """
    View class for handling the checkout process, including retrieving cart items,
    user details, and managing the user's shipping address.
    """

    order_service = OrderApplicationService()

    def get(self, request, session_id):
        response = self.order_service.manage_cart_session(request, session_id)
        return JsonResponse(response, status=200)


def login_required(view_func):
    """
    Decorator to check if the user is authenticated. If not, redirect to the login page.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to proceed to this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


class CheckoutView(View):
    """
    View class for handling the checkout process, including retrieving cart items,
    user details, and managing the user's shipping address.
    """

    cart_service = CartService(log=logger)
    user_service = UserApplicationService(log=logger)

    @method_decorator(login_required)
    def get(self, request):
        """
        Handle GET requests to the checkout page. This method retrieves cart items,
        calculates the total price, gets user details, and manages the shipping address form.
        """
        try:
            logger.info(
                f"Checkout GET request initiated for user: {request.user.username}"
            )
            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                logger.warning(
                    f"User {request.user.username} attempted to checkout with an empty cart."
                )
                messages.error(request, "Your cart is empty.")
                return redirect("cart_page")

            # Get user details for name display
            user_first_name, user_last_name = (
                self.cart_service.get_user_details_by_username(request.user.username)
            )

            # Calculate total price
            total = sum(item.total_price for item in cart_items)
            logger.info(f"Total price calculated: {total}")

            saved_address = self.user_service.get_user_addresses(
                request.user, single=True
            )
            if saved_address:
                logger.info(
                    f"Redirecting user {request.user.username} to order summary page."
                )
                return redirect("order_summary")

            # Initialize form with saved address data if present
            initial_data = {}
            if saved_address:
                initial_data = {
                    "flat_building": saved_address.get("flat_building", ""),
                    "area": saved_address.get("area", " "),
                    "landmark": saved_address.get("landmark", ""),
                    "city": saved_address.get("city", ""),
                    "state": saved_address.get("state", ""),
                    "pincode": saved_address.get("pincode", ""),
                }

            form = UserAddressForm(initial=initial_data)

            logger.info(f"Rendering checkout page for user: {request.user.username}")
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
                },
            )

        except Exception as e:
            logger.error(
                f"Error during checkout for user {request.user.username}: {str(e)}"
            )
            messages.error(request, "An error occurred during checkout.")
            return redirect("cart_page")

    @method_decorator(login_required)
    def post(self, request):
        """
        Handle POST requests to the checkout page. This method processes the shipping
        address form, creates or updates the user's address, and redirects to the order summary page.
        """
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
                logger.info(
                    f"Address {address.id} created/updated for user: {request.user.username}"
                )
                # Optionally, save the address to session
                request.session["shipping_address"] = {
                    "flat_building": address.flat_building,
                    "area": address.area,
                    "landmark": address.landmark,
                    "city": address.city,
                    "state": address.state,
                    "pincode": address.pincode,
                }
                return redirect("order_summary")

            # If form is invalid, re-render checkout page with form errors
            cart_items = self.cart_service.get_cart_items(request.user, request)
            total = sum(item.total_price for item in cart_items)
            messages.error(request, "There was an error with your shipping address.")
            logger.warning(
                f"Invalid address form submission for user {request.user.username}."
            )
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
    """
    View class for displaying the order summary, including retrieving cart items,
    calculating the total price, and displaying user addresses.
    """

    cart_service = CartService(log=logger)
    user_service = UserApplicationService(log=logger)
    order_service = OrderApplicationService()

    @method_decorator(login_required)
    def get(self, request):
        """
        Handle GET requests to the order summary page. This method retrieves cart items,
        calculates the total price, and gets user addresses.
        """
        try:
            logger.info(
                f"Order summary GET request initiated for user: {request.user.username}"
            )

            cart_items = self.cart_service.get_cart_items(request.user, request)
            if not cart_items:
                messages.error(request, "Your cart is empty.")
                logger.info(
                    f"Order summary GET request initiated for user: {request.user.username}"
                )

                return redirect("cart_page")

            total = sum(item.total_price for item in cart_items)
            logger.info(f"Total price calculated: {total}")

            addresses = self.user_service.get_user_addresses(request.user, single=False)
            logger.info(f"Retrieved addresses for user: {request.user.username}")

            return render(
                request,
                "order_summary.html",
                {
                    "cart_items": cart_items,
                    "total": total,
                    "addresses": addresses,
                },
            )
        except Exception as e:
            logger.error(f"Error displaying order summary: {str(e)}")
            messages.error(
                request, "An error occurred while displaying the order summary."
            )
            return redirect("cart_page")


class PlaceOrderView(View):
    """
    View class for handling the order placement process. This includes validating the user's authentication status,
    retrieving the shipping address, creating the order, and emptying the cart after successful order placement.
    """

    user_service = UserApplicationService(log=logger)
    order_service = OrderApplicationService()

    @method_decorator(login_required)
    def post(self, request):
        """
        Handle POST requests to place an order. This method validates the user, retrieves the shipping address,
        creates the order, and empties the cart.
        """
        try:
            logger.info(
                f"Order placement POST request initiated for user: {request.user.username}"
            )
            if request.user.is_authenticated:
                logger.info(f"User {request.user.username} is authenticated")
                shipping_address_id = request.POST.get("shipping_address")
                payment_method = request.POST.get("paymentMethod")
                logger.debug(f"Shipping address ID received: {shipping_address_id}")
                logger.debug(f"Payment method received: {payment_method}")

                if not shipping_address_id:
                    messages.error(
                        request,
                        "No shipping address selected. Please select one before placing your order.",
                    )
                    logger.warning(
                        f"No shipping address selected by user {request.user.username}"
                    )
                    return redirect("order_summary")  # Redirect back to order summary

                if not payment_method:
                    messages.error(
                        request,
                        "No payment method selected. Please select one before placing your order.",
                    )
                    logger.warning(
                        f"No payment method selected by user {request.user.username}"
                    )
                    return redirect("order_summary")

                # Fetch the address details using the ID
                address = self.user_service.get_address_by_id(
                    request.user, shipping_address_id
                )

                if not address:
                    messages.error(request, "Invalid shipping address.")
                    logger.warning(
                        f"Invalid shipping address ID {shipping_address_id} for user {request.user.username}"
                    )
                    return redirect("order_summary")

                order = self.order_service.create_order(
                    request.user, address, payment_method=payment_method
                )

                if order:
                    # Loop through order items and update product stock
                    for item in order.items.all():
                        product = item.product
                        if product.quantity >= item.quantity:
                            # Update the stock by deducting the quantity of the ordered item
                            product.quantity -= item.quantity
                            product.save()
                        else:
                            # Optionally handle the case where there's insufficient stock
                            messages.error(
                                request,
                                f"Insufficient stock for {product.title}. Please reduce quantity.",
                            )
                            return redirect("order_summary")

                self.order_service.empty_cart(request.user)

                # Show success message
                messages.success(request, "Your order has been placed successfully!")
                logger.info(
                    f"Order {order.id} placed successfully for user {request.user.username}"
                )
                return redirect("order_confirmation", order_id=order.id)

            else:
                messages.error(request, "You need to be logged in to place an order.")
                logger.warning(
                    f"Unauthenticated order placement attempt by user: {request.user}"
                )
                return redirect("login")

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            messages.error(request, "An error occurred while placing your order.")
            return redirect("checkout")


class EditAddressView(View):
    """
    View class for handling the editing of a user's address. This includes displaying the address form
    with the current address data for GET requests, and updating the address for POST requests.
    """

    user_service = UserApplicationService(log=logger)

    @method_decorator(login_required)
    def get(self, request):
        """
        Handle GET requests to display the address editing form with the current address data.
        """
        try:
            logger.info(
                f"Edit address GET request initiated by user: {request.user.username}"
            )
            address_id = request.GET.get("address_id")
            logger.debug(f"Address ID received: {address_id}")

            if not address_id:
                messages.error(request, "Invalid address ID.")
                return redirect("checkout")

            # Retrieve the address to edit
            address = self.user_service.get_address_by_id(request.user, address_id)
            if not address:
                logger.warning(
                    f"Address ID {address_id} not found for user: {request.user.username}"
                )
                messages.error(request, "Address not found.")
                return redirect("checkout")

            # Initialize the form with the current address data
            form = UserAddressForm(instance=address)
            logger.info(
                f"Address form initialized for editing by user: {request.user.username}"
            )
            return render(request, "edit_address.html", {"form": form})

        except Exception as e:
            messages.error(request, "Error while loading the address form.")
            return redirect("checkout")

    @method_decorator(login_required)
    def post(self, request):
        """
        Handle POST requests to update the user's address with the submitted form data.
        """

        try:
            logger.info(
                f"Edit address POST request initiated by user: {request.user.username}"
            )
            address_id = request.GET.get("address_id")
            logger.debug(f"Address ID received: {address_id}")
            address = self.user_service.get_address_by_id(request.user, address_id)

            # Populate the form with POST data and the current address instance
            form = UserAddressForm(request.POST, instance=address)

            if form.is_valid():
                # Save the updated address
                form.save()
                messages.success(request, "Address updated successfully.")
                logger.info(
                    f"Address ID {address_id} updated successfully for user: {request.user.username}"
                )
                return redirect("order_summary")
            else:
                messages.error(request, "Please correct the errors below.")
                logger.warning(
                    f"Form validation errors for user: {request.user.username}"
                )
            return render(request, "edit_address.html", {"form": form})

        except Exception as e:
            logger.error(
                f"Error while updating the address for user {request.user.username}: {str(e)}"
            )
            messages.error(request, "Error while updating the address.")
            return redirect("checkout")


class SetDefaultAddressView(View):
    """
    View class for handling the setting of a default address for a user.
    """

    user_service = UserApplicationService(log=logger)

    def post(self, request):
        """
        Handle POST requests to set a user's address as the default address.
        """

        try:
            logger.info(
                f"Set default address POST request initiated by user: {request.user.username}"
            )
            address = self.user_service.get_user_addresses(request.user, single=True)

            logger.debug(
                f"Address retrieved for user {request.user.username}: {address}"
            )
            self.user_service.set_default_address(request.user, address)
            logger.info(f"Address set as default for user: {request.user.username}")
            messages.success(request, "Address has been set as default.")
            return redirect("order_summary")

        except Exception as e:
            logger.error(
                f"Error setting default address for user {request.user.username}: {str(e)}"
            )
            messages.error(request, "Error setting default address.")
            return redirect("checkout")


class OrderConfirmationView(TemplateView):
    """
    View class for displaying the order confirmation page.
    """

    template_name = "order_confirmation.html"
    order_service = OrderApplicationService()

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle the logic before rendering the template.
        """
        order_id = self.kwargs.get("order_id")

        if not order_id:
            logger.error("Order ID is required to render the order confirmation page.")
            messages.error(self.request, "Order ID is required to render this page.")
            return redirect("cart_page")  # Redirect if order_id is missing

        try:
            # Fetch the order using the updated method
            order = self.order_service.get_order_by_id(order_id)
        except ValueError as e:
            # Log the error and show a user-friendly message
            logger.error(f"Error fetching order with ID {order_id}: {str(e)}")
            messages.error(
                self.request, str(e)
            )  # Display the error message to the user
            return redirect("cart_page")  # Redirect to the cart or home page

        # If order exists, proceed to generate the context
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Retrieve context data for rendering the template.
        """
        # Initialize context
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get("order_id")

        # Fetch the order again after redirect check in dispatch
        try:
            order = self.order_service.get_order_by_id(order_id)
        except ValueError:
            # If order is not found, return empty context or an appropriate message
            context["error_message"] = "The order with the specified ID does not exist."
        else:
            context["order"] = order
            context["order_id"] = order_id

        logger.info(f"Order confirmation page loaded for order ID {order_id}.")
        return context


class DownloadInvoiceView(View):
    """
    View class for handling the download of an order invoice as a PDF.
    """

    order_service = OrderApplicationService()

    @method_decorator(login_required)
    def get(self, request, order_id):
        """
        Handle GET requests to download the invoice for an order.
        """
        try:
            # Call the service method to generate the invoice PDF
            pdf, error_message = self.order_service.generate_invoice_pdf(order_id)
            if error_message:
                return HttpResponse(error_message, status=404)

            # Create a response object with PDF content type
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="invoice_{order_id}.pdf"'
            )

            # Write the PDF content to the response
            response.write(pdf)
            logger.info(f"Invoice generated and downloaded for order ID {order_id}.")
            return response

        except Exception as e:
            logger.error(f"Error generating invoice for order ID {order_id}: {str(e)}")
            return HttpResponse(
                "An error occurred while generating the invoice.", status=500
            )


@method_decorator(csrf_exempt, name="dispatch")
class RemoveAddressView(View):
    """
    CBV to handle the removal of an address.
    """

    @method_decorator(login_required)
    def delete(self, request, address_id):
        """
        Handles the request to remove an address by its ID.

        Args:
            request: The HTTP request object.
            address_id: The ID of the address to remove.

        Returns:
            JsonResponse: A JSON response indicating success or failure.
        """
        try:

            address_service = UserApplicationService(log=logger)
            success = address_service.remove_address(address_id)
            if success:
                logger.info(f"Address with ID {address_id} successfully removed.")
                return JsonResponse({"success": True}, status=200)
            else:
                logger.warning(f"Address with ID {address_id} not found.")
                return JsonResponse(
                    {"success": False, "message": "Address not found"}, status=404
                )
        except Exception as e:
            logger.error(f"Error removing address with ID {address_id}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "message": "An error occurred while removing the address",
                },
                status=500,
            )


class UserProfileView(View):
    @method_decorator(login_required)
    def get(self, request):
        """
        Renders the user profile page with order history.

        This view fetches the order history of the currently logged-in user
        and renders it on the "profile.html" page.
        """
        user_profile_service = OrderApplicationService()
        order_history = user_profile_service.get_order_history(request.user)

        return render(request, "profile.html", {"order_history": order_history})


class UpdateAddressView(View):
    """
    View class for handling the updating of a user's address via a JSON request.
    """

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to update a user's address with the provided JSON data.
        """

        data = json.loads(request.body)

        address_id = data.get("id")
        flat_building = data.get("flat_building")
        area = data.get("area")
        landmark = data.get("landmark")
        city = data.get("city")
        pincode = data.get("pincode")
        state=data.get("state")

        try:
            logger.info(
                f"Update address POST request initiated by user: {request.user.username}"
            )
            user_service = UserApplicationService(log=logger)

            address = user_service.get_address_by_id(request.user, address_id)
            address.flat_building = flat_building
            address.area = area
            address.landmark = landmark
            address.city = city
            address.pincode = pincode
            address.state=state
           
            address.save()
            
            logger.debug(
                f"Received data for updating address ID {address_id} for user {request.user.username}"
            )

            return JsonResponse({"success": True})
        except Exception as e:
            logger.error(
                f"Error updating address for user {request.user.username}: {str(e)}"
            )
            return JsonResponse({"success": False, "message": "Address not found"})


class TrackOrderView(View):
    @method_decorator(login_required)
    def get(self, request, order_id):
        """
        Renders the order tracking page for a specific order.

        This view fetches the status of a particular order and renders it
        on the "track_order.html" page.
        """
        user_profile_service = OrderApplicationService()
        order = user_profile_service.track_order(request.user, order_id)
        if order:
            return render(request, "track_order.html", {"order": order})
        else:
            return redirect("profile")



class CancelOrderView(View):
    @method_decorator(login_required)
    def post(self, request, order_id):
        """
        Cancels an order for the logged-in user.

        This view attempts to cancel an order by its ID for the currently logged-in
        user and returns a JSON response indicating success or failure.
        """
        user_profile_service = OrderApplicationService()
        order = user_profile_service.cancel_order(request.user, order_id)

        if order:
            # If the order was successfully cancelled
            return JsonResponse(
                {"success": True, "message": "Order has been cancelled successfully."}
            )
        else:
            # If the order wasn't found or couldn't be cancelled
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unable to cancel order. Please try again.",
                }
            )






class ChangePasswordView(View):
    def post(self, request, *args, **kwargs):
        print('herlolllllllooooooooooooooooo')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        re_new_password = request.POST.get('re_new_password')

        # Check if the old password is correct
        if not request.user.check_password(old_password):
            return JsonResponse({'error': 'Old password is incorrect'}, status=400)

        # Ensure the new password and re-entered new password match
        if new_password != re_new_password:
            return JsonResponse({'error': 'New passwords do not match'}, status=400)

        # Update the user's password
        try:
            user = request.user
            user.set_password(new_password)
            user.save()

            # Update the session with the new password (important for keeping the user logged in)
            update_session_auth_hash(request, user)

            return JsonResponse({'success': 'Password updated successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
