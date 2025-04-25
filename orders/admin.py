from django.contrib import admin
from .models import Order, OrderItem, ShippingRate, PaymentTransaction

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'variant_name', 'price', 'discount_price', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'final_price', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('user_email', 'shipping_name', 'shipping_phone')
    readonly_fields = ('total_price', 'final_price', 'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at')
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'total_price', 'shipping_cost', 'discount', 'final_price')
        }),
        ('Shipping Details', {
            'fields': ('shipping_name', 'shipping_phone', 'shipping_address', 'shipping_province', 
                       'shipping_city', 'shipping_postal_code', 'shipping_courier', 'shipping_tracking_number')
        }),
        ('Payment Info', {
            'fields': ('payment_method', 'payment_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at')
        }),
    )
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'variant_name', 'price', 'quantity', 'subtotal')
    search_fields = ('product_name', 'variant_name')
    readonly_fields = ('subtotal',)

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ('origin_city', 'destination_city', 'courier', 'service', 'cost', 'estimated_days')
    list_filter = ('courier', 'created_at')
    search_fields = ('origin_city', 'destination_city')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'transaction_id', 'payment_type', 'amount', 'status', 'transaction_time')
    list_filter = ('status', 'payment_type', 'transaction_time')
    search_fields = ('order__id', 'transaction_id')
    readonly_fields = ('transaction_id', 'transaction_time', 'created_at', 'updated_at', 'raw_response')