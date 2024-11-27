from django.contrib import admin
from .models import OrderItem,Orders

admin.site.register(Orders)
admin.site.register(OrderItem)