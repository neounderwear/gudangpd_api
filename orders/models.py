from django.db import models
from django.conf import settings
from products.models import ProductVariant

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Shipping information
    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_province = models.CharField(max_length=100)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_courier = models.CharField(max_length=50, blank=True)
    shipping_tracking_number = models.CharField(max_length=100, blank=True)
    
    # Payment information
    payment_method = models.CharField(max_length=50, blank=True)
    payment_details = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    def calculate_total_price(self):
        """Calculate the total price of the order"""
        self.total_price = sum(item.subtotal for item in self.items.all())
        self.final_price = self.total_price + self.shipping_cost - self.discount
        return self.final_price
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            super().save(*args, **kwargs)
            self.calculate_total_price()
            kwargs.pop('force_insert', None)
            return super().save(*args, **kwargs)
        else:
            self.calculate_total_price()
            return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, related_name='order_items')
    
    # Store product details at time of order (in case product changes later)
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # If this is a new order item being created, update product info
        if not self.pk and self.product_variant:
            self.product_name = self.product_variant.product.name
            self.variant_name = self.product_variant.name
            
            # Use discount price if available, otherwise use regular price
            if self.product_variant.discount_price:
                self.price = self.product_variant.discount_price
                self.discount_price = self.product_variant.discount_price
            else:
                self.price = self.product_variant.price
                
        # Calculate subtotal
        effective_price = self.discount_price if self.discount_price else self.price
        self.subtotal = effective_price * self.quantity
        
        super().save(*args, **kwargs)
        
        # Update order total
        if self.order:
            self.order.calculate_total_price()
            self.order.save()
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name} - {self.variant_name}"


class ShippingRate(models.Model):
    """Model to store shipping rates fetched from RajaOngkir API"""
    origin_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    courier = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Create a unique constraint to avoid duplicate shipping rates
        unique_together = ('origin_city', 'destination_city', 'courier', 'service')
    
    def __str__(self):
        return f"{self.origin_city} to {self.destination_city} via {self.courier} {self.service}"


class PaymentTransaction(models.Model):
    """Model to store payment transaction records from Midtrans"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    transaction_time = models.DateTimeField()
    transaction_status = models.CharField(max_length=50)
    fraud_status = models.CharField(max_length=50, blank=True, null=True)
    raw_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} for Order #{self.order.id}"