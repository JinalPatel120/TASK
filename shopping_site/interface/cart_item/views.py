from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from shopping_site.application.cart_item.services import CartService
from shopping_site.application.product.services import ProductApplicationService
from django.contrib import messages
from shopping_site.infrastructure.logger.models import logger



class AddToCartView(View):
    cart_service=CartService(log=logger)
    """
    View to handle adding a product to the cart. 
    It checks whether the user is authenticated or anonymous and adds the product to the appropriate cart.
    """
    def post(self, request, product_id):

        """
        Handles the POST request for adding a product to the cart.
        """
        try:
            product = ProductApplicationService.get_product_by_id(product_id)
            quantity = int(request.POST.get("quantity", 1))

             # Validate if the quantity is less than or equal to 0
            if quantity <= 0:
                messages.error(request, "The quantity must be a positive number.")
                return redirect('product_detail', product_id=product.id)
            
            if quantity > product.quantity:
                    messages.error(request, f"Sorry, only {product.quantity} of this product is available.")
                    return redirect('product_detail', product_id=product.id)
            
            if request.user.is_authenticated:
                cart = self.cart_service.get_or_create_cart_for_user(request.user)
            else:
                cart = self.cart_service.get_or_create_cart_for_anonymous_user(request.session.session_key)

            # Add the product to the cart
            self.cart_service.add_product_to_cart(cart, product, quantity)
            messages.success(request, f'{product.title} has been added to your cart.')
            return redirect('cart_page')  
        
        except Exception as e:
            # Log the error and show a generic message to the user
            logger.error(f"Error adding product {product_id} to cart: {str(e)}")
            messages.error(request, "An error occurred while adding the product to your cart. Please try again.")
            return redirect('product_list')  # Redirect to the product list or another page

        



class CartView(View):
    cart_service=CartService(log=logger)
    """
    View to display the user's cart with all items and the total price.
    """
    def get(self, request):
        """
        Handles the GET request for displaying the cart.
        """
        try:
            # Fetch the cart items for the user
            cart_items = self.cart_service.get_cart_items(request.user, request)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            messages.error(
                self.request, "An error occurred while processing your request."
            )
            return redirect('product_list')  # Redirect to the product listing if no cart is found

     
        total = sum(item.total_price for item in cart_items) 
        return render(request, 'view_cart.html', {'cart_items': cart_items,'total':total})




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
