from rest_framework import serializers
from .models import Brand, Category, Product, ProductVariant

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'brand_name', 'image_url', 'created_at']
        read_only_fields = ['created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'image_url', 'created_at']
        read_only_fields = ['created_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'price', 'reseller_price', 
            'sku', 'stock', 'weight', 'created_at', 'updated_at', 'discount_price'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProductVariantInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'price', 'reseller_price', 
            'sku', 'stock', 'weight', 'discount_price'
        ]

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantInlineSerializer(many=True, read_only=True)
    brand_name = serializers.CharField(source='brand.brand_name', read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'brand_name',
            'category', 'category_name', 'image_url', 
            'created_at', 'updated_at', 'variants'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProductDetailSerializer(serializers.ModelSerializer):
    variants = ProductVariantInlineSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 
            'category', 'image_url', 'created_at', 
            'updated_at', 'variants'
        ]
        read_only_fields = ['created_at', 'updated_at']