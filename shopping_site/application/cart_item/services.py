from shopping_site.domain.product.models import Product
from shopping_site.domain.cart_item.models import Cart, CartItem
from shopping_site.domain.authentication.models import User
from django.db import IntegrityError
from typing import List
from shopping_site.infrastructure.logger.models import AttributeLogger
from django.contrib.sessions.models import Session
from django.utils.timezone import now
import uuid
from django.db.models import F, ExpressionWrapper, DecimalField, Sum,Q
from typing import Optional, Tuple, Dict


class CartService:
    """
    Service class responsible for managing cart-related operations,
    including creating carts, adding products to the cart, and updating the cart.
    """

    def __init__(self, log: AttributeLogger) -> None:
        self.log = log  # Store the logger instance

    def get_or_create_cart_for_user(self, user) -> Cart:
        """Fetch or create a cart for a logged-in user"""
        print('Cart.objects.get_or_create(user=user, is_active=True)',Cart.objects.get_or_create(user=user, is_active=True))
        cart, created = Cart.objects.get_or_create(user=user, is_active=True)
        print(cart,'cart')
        return cart

    def get_or_create_cart_for_anonymous_user(self, session_key: str) -> Cart:
        """Fetch or create a cart for an anonymous user based on session"""

        if not session_key:
            # Generate a new session key if none exists
            session_key = str(uuid.uuid4())  # Generate a unique session key

        # Fetch or create a cart associated with the session_key
        cart, created = Cart.objects.get_or_create(
            session_key=session_key, is_active=True
        )

        # Return the cart
        return cart

    
    def add_product_to_cart(
        self, cart: Cart, product: Product, quantity: int
    ) -> CartItem:
        """Add or update product quantity in the cart"""
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.save()
        cart.update_total()
        return cart_item

    def get_user_details_by_username(
        self, username: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve the first and last name of a user by their username.

        Args:
            username (str): The username of the user to retrieve details for.
        """

        try:
            user = User.objects.get(username=username)
            return user.first_name, user.last_name
        except User.DoesNotExist:
            return None, None

    def get_cart_items(self, user, request) -> List[CartItem]:
        """
        Retrieve all items in the user's cart (authenticated or anonymous).
        """
        cart = Cart.objects.filter(
                Q(user=user) if user.is_authenticated else Q(session_key=request.session.session_key)
            ).first()


        if cart:
            # Fetch cart items with related products and annotate total_price in the query
            cart_items = (
                CartItem.objects.filter(cart=cart)
                .select_related("product")
                .annotate(
                    total_price=ExpressionWrapper(
                        F("quantity") * F("product__price"), output_field=DecimalField()
                    )
                )
            )
            return cart_items
        return []

    def update_cart_item_quantity(self, item_id: int, quantity: int) -> CartItem:
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

            return (
                item,
                f"Only {available_quantity} items were available, so the quantity has been updated.",
            )
        else:
            # Update the cart item if the requested quantity is valid
            if quantity > 0:
                item.quantity = quantity
                item.save()
                return item, f"Cart item {product} quantity updated successfully."

        # In case of invalid quantity (e.g., negative or zero)
        return item, "Quantity must be a positive number."

    def remove_cart_item(self, item_id: int) -> None:
        """
        Remove a product from the cart by deleting the CartItem.

        Args:
            item_id (int): The ID of the CartItem to be removed.
        """

        item = CartItem.objects.get(id=item_id)
        item.delete()

    def get_cart_item_count(self, cart: Cart) -> int:
        """
        This method returns the total number of items in the cart.
        It sums the quantity of each product in the cart.

        Args:
            cart (Cart): The cart object containing the items.
        """
        try:
            # Ensure cart is a valid Cart object and check if it has related CartItems
            if cart and hasattr(cart, "items"):
                cart_items = cart.items.all()  # Use .all() to fetch the related items
                return sum(item.quantity for item in cart_items)
            else:
                return 0
        except Exception as e:
            return 0

    def get_product_quantity_in_cart(self, cart: Cart, product: Product) -> int:
        """
        Retrieve the quantity of a specific product in the cart.

        Args:
            cart (Cart): The cart object containing the items.
            product (Product): The product for which quantity is checked.

        Returns:
            int: The quantity of the specified product in the cart.
        """
        cart_item = cart.items.filter(product=product).first()
        return cart_item.quantity if cart_item else 0
