from shopping_site.domain.product.models import Product
from shopping_site.domain.cart_item.models import Cart, CartItem
from django.db import IntegrityError
from typing import List
from shopping_site.infrastructure.logger.models import AttributeLogger
from django.contrib.sessions.models import Session
from django.utils.timezone import now
import uuid

class CartService:
    """
    Service class responsible for managing cart-related operations,
    including creating carts, adding products to the cart, and updating the cart.
    """
    
    def __init__(self, log: AttributeLogger) -> None:
        self.log = log  # Store the logger instance



    def get_or_create_cart_for_user(self,user) -> Cart:
        """Fetch or create a cart for a logged-in user"""
        cart, created = Cart.objects.get_or_create(user=user, is_active=True)
        return cart

  
    # def get_or_create_cart_for_anonymous_user(self,session_key:str) -> Cart:
    #     """Fetch or create a cart for an anonymous user based on session"""
    #     print('session key',session_key)
    #     cart, created = Cart.objects.get_or_create(session_key=session_key, is_active=True)
    #     return cart

    def get_or_create_cart_for_anonymous_user(self, session_key: str) -> Cart:
        """Fetch or create a cart for an anonymous user based on session"""
        

        if not session_key:
            # Generate a new session key if none exists
            session_key = str(uuid.uuid4())  # Generate a unique session key
        
 
        # Fetch or create a cart associated with the session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, is_active=True)
        
        # Return the cart
        return cart


    def add_product_to_cart(self,cart:Cart, product:Product, quantity:int) -> CartItem:
        """Add or update product quantity in the cart"""
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.save()
        cart.update_total()
        return cart_item

 
 
    def get_cart_items(self,user, request) -> List[CartItem]:
        """
        Retrieve all items in the user's cart (authenticated or anonymous).
        """
        # Check if the user is authenticated
        if user.is_authenticated:
            # For authenticated users, fetch the cart using user UUID
            cart = Cart.objects.filter(user=user).first()
        else:
            # For anonymous users, use the session key from request
            session_key = request.session.session_key if request.session.session_key else None
            cart = Cart.objects.filter(session_key=session_key).first()
            print('cart items',cart.items.all() if cart else [])

        return cart.items.all() if cart else []
    
    
    def update_cart_item_quantity(self,item_id:int, quantity:int) -> CartItem:
        """
        Update the quantity of an existing cart item
        """
        item = CartItem.objects.get(id=item_id)
        product = item.product 

      

        # Check if the requested quantity is more than the available stock
        if quantity > product.quantity:
            # Notify the user about the stock limitation (you could store this in a message system or directly return a message)
            available_quantity = product.quantity
            item.quantity = available_quantity
            item.save()

            # Optionally, return a message to notify the user that the quantity was adjusted
            return item, f"Only {available_quantity} items were available, so the quantity has been updated."
        else:
            # Update the cart item if the requested quantity is valid
            if quantity > 0:
                item.quantity = quantity
                item.save()
                return item, f"Cart item {product} quantity updated successfully."

        # In case of invalid quantity (e.g., negative or zero)
        return item, "Quantity must be a positive number."

    def remove_cart_item(self,item_id:int):
        """
        Remove a product from the cart by deleting the CartItem.
        """
        item = CartItem.objects.get(id=item_id)
        item.delete()

    def get_cart_item_count(self, cart):
        """
        This method returns the total number of items in the cart.
        It sums the quantity of each product in the cart.
        """
        # Ensure `cart.items` is a queryset and not a RelatedManager
        cart_items = cart.items.all()  # Use .all() to fetch the related items

        # Now, sum the quantities of the items in the cart
        return sum(item.quantity for item in cart_items)
