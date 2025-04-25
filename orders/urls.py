from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, ShippingRateViewSet, CalculateShippingView,
    CreatePaymentView, PaymentNotificationView
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'shipping-rates', ShippingRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calculate-shipping/', CalculateShippingView.as_view(), name='calculate-shipping'),
    path('orders/<int:order_id>/create-payment/', CreatePaymentView.as_view(), name='create-payment'),
    path('payment-notification/', PaymentNotificationView.as_view(), name='payment-notification'),
]