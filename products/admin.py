from django.contrib import admin
from .models import Brand, Category, Product, ProductVariant

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand_name', 'created_at')
    search_fields = ('brand_name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'created_at')
    search_fields = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'brand', 'category', 'created_at', 'updated_at')
    list_filter = ('brand', 'category')
    search_fields = ('name', 'description')
    inlines = [ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'name', 'price', 'reseller_price', 'stock', 'sku')
    list_filter = ('product',)
    search_fields = ('name', 'sku')