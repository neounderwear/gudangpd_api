from rest_framework import serializers
from .models import Order, OrderItem, ShippingRate, PaymentTransaction
from products.serializers import ProductVariantSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_variant', 'product_name', 'variant_name',
            'price', 'discount_price', 'quantity', 'subtotal'
        ]
        read_only_fields = ['product_name', 'variant_name', 'subtotal']
    
    def validate_product_variant(self, value):
        if value.stock < self.initial_data.get('quantity', 1):
            raise serializers.ValidationError("Not enough stock available")
        return value
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_variant', 'quantity']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, read_only=False, required=True)
    
    class Meta:
        model = Order
        fields = [
            'shipping_name', 'shipping_phone', 'shipping_address',
            'shipping_province', 'shipping_city', 'shipping_postal_code',
            'items'
        ]
        
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        return value

    def create(self, validated_data):
        if 'id' in validated_data:
            validated_data.pop('id')

        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        order = Order.objects.create(user=user, **validated_data)
        
        for item_data in items_data:
            product_variant = item_data['product_variant']
            quantity = item_data['quantity']
            
            if product_variant.stock < quantity:
                order.delete()
                raise serializers.ValidationError(f"Not enough stock for {product_variant.name}")
            
            OrderItem.objects.create(order=order, **item_data)
            
            product_variant.stock -= quantity
            product_variant.save()
        
        order.calculate_total_price()
        order.save()
        
        return order


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_variant_details = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_variant', 'product_name', 'variant_name',
            'price', 'discount_price', 'quantity', 'subtotal',
            'product_variant_details'
        ]
    
    def get_product_variant_details(self, obj):
        if obj.product_variant:
            return ProductVariantSerializer(obj.product_variant).data
        return None


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'total_price', 'shipping_cost', 
            'discount', 'final_price', 'created_at', 'updated_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_price', 'shipping_cost', 'discount', 'final_price',
            'shipping_name', 'shipping_phone', 'shipping_address', 'shipping_province',
            'shipping_city', 'shipping_postal_code', 'shipping_courier', 'shipping_tracking_number',
            'payment_method', 'payment_details', 'created_at', 'updated_at',
            'paid_at', 'shipped_at', 'delivered_at', 'items'
        ]
        read_only_fields = [
            'user', 'total_price', 'final_price', 'created_at', 'updated_at',
            'paid_at', 'shipped_at', 'delivered_at'
        ]


class ShippingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRate
        fields = '__all__'


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ['order', 'transaction_id', 'transaction_time', 'created_at', 'updated_at']


class ShippingCostRequestSerializer(serializers.Serializer):
    origin_city = serializers.CharField()
    destination_city = serializers.CharField()
    weight = serializers.IntegerField(min_value=1)
    courier = serializers.CharField()