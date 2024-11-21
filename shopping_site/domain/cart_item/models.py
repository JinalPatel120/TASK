from django.db import models
from shopping_site.utils.custom_models import TimestampedModel
from shopping_site.domain.authentication.models import User
from shopping_site.domain.product.models import Product


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Link to user, optional
    created_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    is_active = models.BooleanField(default=True)
    
    @property
    def total(self):
        return sum(item.quantity * item.product.price for item in self.items.all())
    
    def update_total(self):
        # Update the cart's total price based on the items
        total_price = sum(item.quantity * item.product.price for item in self.items.all())
        self.total_price = total_price
        self.save()

    def __str__(self):
        return f"Cart {self.id} - Total: ${self.total}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Link to your product model
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"