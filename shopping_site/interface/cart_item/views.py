from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from shopping_site.application.cart_item.services import CartService
from shopping_site.application.product.services import ProductApplicationService
from django.contrib import messages
from shopping_site.infrastructure.logger.models import logger
from django.http import JsonResponse

class AddToCartView(View):
    cart_service = CartService(log=logger)

    def post(self, request, product_id):
        """
        Handles the POST request for adding a product to the cart.
        """
   
        try:
            if not request.session.session_key:
                request.session.create()  # Ensure session key is created

            product = ProductApplicationService.get_product_by_id(product_id)
            quantity = int(request.POST.get("quantity", 1))

            # Validate if the quantity is less than or equal to 0
            if quantity <= 0:
                return JsonResponse({'error': 'The quantity must be a positive number.'}, status=400)
            
            if quantity > product.quantity:
                return JsonResponse({'error': f"Sorry, only {product.quantity} of this product is available."}, status=400)
            
            if request.user.is_authenticated:
                cart = self.cart_service.get_or_create_cart_for_user(request.user)
                request.session.modified = True
            else:
                cart = self.cart_service.get_or_create_cart_for_anonymous_user(request.session.session_key)
            


            # Add the product to the cart
            self.cart_service.add_product_to_cart(cart, product, quantity)
          
            # Return updated cart count
            cart_count = self.cart_service.get_cart_item_count(cart)
            messages.success(request, f"Product {product.title} has been {'added to' if quantity == 1 else 'updated in'} your cart!")
            message= f"Product {product.title} has been {'added to' if quantity == 1 else 'updated in'} your cart!"
            return JsonResponse({ 'cart_count': cart_count,'message': message})

        except Exception as e:
            logger.error(f"Error adding product {product_id} to cart: {str(e)}")
            return JsonResponse({'error': 'An error occurred while adding the product to your cart.'}, status=500)


class UpdateCartCountView(View):
    cart_service = CartService(log=logger)

    def get(self, request):
        try:
            if not request.session.session_key:
                request.session.create()  # Ensure session key is created

            if request.user.is_authenticated:
                cart = self.cart_service.get_or_create_cart_for_user(request.user)
            else:
                cart = self.cart_service.get_or_create_cart_for_anonymous_user(request.session.session_key)
                request.session.modified = True

            cart_count = self.cart_service.get_cart_item_count(cart)
 
            return JsonResponse({'cart_count': cart_count})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# class CartView(View):
#     cart_service = CartService(log=logger)

#     def get(self, request):
#         """
#         Handles the GET request for displaying the cart.
#         """
#         try:
#             # Fetch the cart items for the user
#             cart_items = self.cart_service.get_cart_items(request.user, request)

#             # Calculate the total cost of the cart
#             total = sum(item.total_price for item in cart_items)
        
#             # Get cart item count
     
#             return render(request, 'view_cart.html', {
#                 'cart_items': cart_items,
#                 'total': total,
            
#             })
#         except Exception as e:
#             logger.error(f"An error occurred: {str(e)}")
#             messages.error(self.request, "An error occurred while processing your request.")
#             return redirect('product_list')  # Redirect to the product listing if no cart is found

class CartView(View):
    cart_service = CartService(log=logger)

    def get(self, request):
        """
        Handles the GET request for displaying the cart.
        """
        try:
            # Fetch the cart items for the user
            cart_items = self.cart_service.get_cart_items(request.user, request)

            # Calculate the total cost of the cart directly from the query
            total = sum(item.total_price for item in cart_items)
        
            return render(request, 'view_cart.html', {
                'cart_items': cart_items,
                'total': total,
            })
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request.")
            return redirect('product_list')  # Redirect to the product listing if no cart is found


class UpdateCartItemView(View):
    """
    View to handle updating the quantity of a cart item.
    """

    cart_service=CartService(log=logger)
    def post(self, request, item_id):
        """
        Handles the POST request for updating the quantity of a cart item.
        """
        try:
            quantity = int(request.POST.get('quantity', 1))

        # Update the cart item quantity using the CartItemService
            item,message=self.cart_service.update_cart_item_quantity(item_id, quantity)

            messages.info(request, message)

        except Exception as e:
            # Handle the case where the cart item is not found
            return redirect('cart_page')  # Redirect to the cart page if the item is not found

        return redirect('cart_page')  # Redirect back to the cart page

class RemoveCartItemView(View):
    cart_service=CartService(log=logger)
    """
    View to handle removing a cart item from the cart.
    """
    def post(self, request, item_id):
        """
        Handles the POST request for removing a cart item.
        """

        try:
            # Remove the cart item using the CartService
            self.cart_service.remove_cart_item(item_id)
        except Exception as e:
            # Handle the case where the cart item is not found
            return redirect('cart_page')  # Redirect to the cart page if the item is not found

        return redirect('cart_page')  # Redirect back to the cart page
