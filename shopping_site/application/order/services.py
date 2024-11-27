from shopping_site.domain.authentication.models import User
from shopping_site.domain.product.models import Product
from shopping_site.domain.order.models import Orders, OrderItem
from django.db import transaction
from typing import List, Type
from django.db import connection
from shopping_site.domain.order.services import OrderService
from shopping_site.domain.cart_item.models import CartItem,Cart
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import Optional,Tuple

class OrderApplicationService:
    """
    Service class responsible for handling order-related operations, such as creating, updating, and retrieving orders.
    """

    @staticmethod
    def get_all_orders() -> List[Orders]:
        """
        This method retrieves all orders.

        Returns:
            List[Orders]: A list of all orders in the database.
        """
        return OrderService.get_all_orders()


       
    @staticmethod
    def create_order(user,address,payment_method):
        """
        This method creates a new order and order items.

        Args:
            user (User): The user who is placing the order.
            items (list of dict): List of items to be ordered. Each item is a dictionary containing
                                  'product' and 'quantity'.

        Returns:
            Orders: The created order.

        Raises:
            ValidationError: If any of the items are invalid.
        """
        # Fetch cart items
  
        cart_items = CartItem.objects.filter(cart__user=user, cart__is_active=True)
        
        # Calculate total price
        total_price = sum(item.product.price * item.quantity for item in cart_items)
      
        # Create the order
        order = Orders.objects.create(
            user=user,
            shipping_address=address,
            payment_method=payment_method,
            total_amount=total_price,
            status='Pending'
        )

   
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price * item.quantity
            )
        

        # Clear the cart items
        user_cart = Cart.objects.filter(user=user, is_active=True).first()
        if user_cart:
            user_cart.is_active = False
            user_cart.save()
   
        return order

    def empty_cart(self, user):
        try:
            # Implement the logic to empty the user's cart
            Cart.objects.filter(user=user).delete()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error emptying cart: {str(e)}")

    @staticmethod
    def update_order_status(order_id: str, new_status: str) -> Orders:
        """
        This method updates the status of an order.

        Args:
            order_id (str): The ID of the order to update.
            new_status (str): The new status to set for the order.

        Returns:
            Orders: The updated order.

        Raises:
            ValueError: If the order does not exist.
        """
        order = OrderService.get_order_by_id(order_id)
        if new_status not in dict(Orders.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
        order.status = new_status
        order.save()
        return order

    @staticmethod
    def get_order_details(order_id: str) -> dict:
        """
        This method retrieves the details of an order, including its items.

        Args:
            order_id (str): The ID of the order to retrieve details for.

        Returns:
            dict: A dictionary containing order details.
        """
        order = OrderService.get_order_by_id(order_id)
        items = OrderItem.objects.filter(order=order)
        return {
            'order_id': order.id,
            'user': order.user.username if order.user else None,
            'order_date': order.order_date,
            'status': order.status,
            'total_amount': order.total_amount,
            'items': [{'product': item.product.title, 'quantity': item.quantity, 'price': item.price} for item in items]
        }

    @staticmethod
    def delete_order(order_id: str) -> None:
        """
        This method deletes an order by its ID.

        Args:
            order_id (str): The ID of the order to delete.
        """
        order = OrderService.get_order_by_id(order_id)
        order.delete()

    def get_order_by_id(self,order_id:str) -> Optional[Orders] :
        """
        Retrieves an order by its ID.
        
        Args:
            order_id (str): The ID of the order to retrieve.
        """
        try:
            return Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return None
    
    def invoice_items(self,order:Orders) -> List[OrderItem]:
        """
        Retrieves the items for a given order.
        
        Args:
            order (Orders): The order whose items are to be retrieved.
        """
        return  OrderItem.objects.filter(order=order)
    
  
    
    def get_order_history(self, user:User) -> List[dict]:
        """
        Retrieves the order history for a given user, including product names.

        Args:
            user (User): The user whose order history is to be fetched.
        """
        orders = Orders.objects.filter(user=user).order_by('-order_date')
        
        # Prepare order data with items' names (product titles)
        order_data = []
        for order in orders:
            item_names = [item.product.title for item in order.items.all()]
            order_data.append({
                "id": order.id,
                "status": order.status,
                "created_at": order.order_date,
                "items": ", ".join(item_names),  
            })
        return order_data


    def track_order(self,user:User, order_id:str) -> Optional[Orders]:
        """
        Tracks an order for a given user by order ID.

        Args:
            user (User): The user whose order is being tracked.
            order_id (str): The ID of the order to track.
        """
        try:
            return Orders.objects.get(id=order_id, user=user)
        except Orders.DoesNotExist:
            return None
        
    def cancel_order(self,user:User,order_id:str) -> Optional[Orders]:
        """ 
        Cancels an order for a given user by order ID.

        Args:
            user (User): The user cancelling the order.
            order_id (str): The ID of the order to cancel."""
        try:
            order=Orders.objects.get(id=order_id, user=user)
            if order.status != 'Cancelled':
                order.status = 'Cancelled'
                order.save()
                return order
            else:
                return None

        except Exception as e:
            return f"an unexpected error occur {str(e)}"

        
    def generate_invoice_pdf(self, order_id:str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Generates a PDF invoice for the given order_id.
        Returns a BytesIO object containing the PDF data.
        """
        try:
            # Retrieve order using order_id
            order = self.get_order_by_id(order_id)
   
            if not order:
                return None, "Order not found."

   
            # Calculate total amount if not already calculated
            if order.total_amount is None:
                order.calculate_total_amount()


      
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, f"Invoice for Order #{order.id}")
            p.drawString(
                100, 725, f"Customer: {order.user.first_name} {order.user.last_name}"
            )


            if isinstance(order, str):
                p.drawString(100, 700, f"Address: {order}")
            else:
                p.drawString(
                    100,
                    700,
                    f"Address: {order}, {order}, {order}",
                )

            p.drawString(100, 675, "Items:")

            
            order_items = self.invoice_items(order=order)

            y = 650
            for item in order_items:
                p.drawString(
                    100, y, f"{item.product} - {item.quantity} x ₹{item.price}"
                )
                y -= 25

            # Draw the total amount
            p.drawString(100, y, f"Total: ₹{order.total_amount}")

            # Finalize the PDF document
            p.showPage()
            p.save()

            # Get PDF content as byte data
            pdf = buffer.getvalue()
            buffer.close()

            return pdf, None

        except Exception as e:
     
            return None, "An error occurred while generating the invoice."

    
