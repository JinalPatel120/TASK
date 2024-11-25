from shopping_site.domain.authentication.models import User
from shopping_site.domain.product.models import Product
from django.db import models
import uuid
from dataclasses import dataclass
from shopping_site.utils.custom_models import TimestampedModel


@dataclass(frozen=True)
class UserID:
    """
    This is a value object that should be used to generate and pass the UserID to the UserFactory.
    """

    value: uuid.UUID


class Orders(TimestampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Order {self.id} by {self.user.username}'
    
    def calculate_total_amount(self):
        """
        Calculate the total amount for the order by summing up the price * quantity
        for each order item.
        """
        total = sum(item.quantity * item.price for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Orders, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product.title}'