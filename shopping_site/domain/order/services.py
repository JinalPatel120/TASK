from shopping_site.domain.authentication.models import User
from shopping_site.domain.product.models import Product
from shopping_site.domain.order.models import Orders, OrderItem
from django.db import transaction
from typing import List, Type
from django.db import connection


class OrderService:
    """
    Service class responsible for handling order-related operations, such as creating, updating, and retrieving orders.
    """

    @staticmethod
    def get_order_by_id(order_id: str) -> Orders:
        """
        This method retrieves an order by its ID.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            Orders: The order with the specified ID.

        Raises:
            ValueError: If the order does not exist.
        """
        try:
            order = Orders.objects.get(id=order_id)
            return order
        except Orders.DoesNotExist:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        
    @staticmethod
    def get_all_orders() -> List[Orders]:
        """
        This method retrieves all orders.

        Returns:
            List[Orders]: A list of all orders in the database.
        """
        return Orders.objects.all()