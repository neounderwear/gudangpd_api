from rest_framework import viewsets
from rest_framework.decorators import action
import uuid
import os
import requests
import base64
import logging
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from .models import Order, ShippingRate, PaymentTransaction
from .serializers import (
    OrderCreateSerializer, OrderListSerializer, OrderDetailSerializer,
    ShippingRateSerializer, ShippingCostRequestSerializer
)

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if order.status not in ['pending', 'paid']:
            return Response(
                {"detail": "Cannot cancel order with status: " + order.status},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item in order.items.all():
            if item.product_variant:
                product_variant = item.product_variant
                product_variant.stock += item.quantity
                product_variant.save()
        
        order.status = 'cancelled'
        order.save()
        
        return Response({"detail": "Order cancelled successfully"})
    
    @action(detail=True, methods=['post'])
    def update_shipping_cost(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'pending':
            return Response(
                {"detail": "Cannot update shipping cost for order with status: " + order.status},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get shipping cost from request
        shipping_cost = request.data.get('shipping_cost')
        shipping_courier = request.data.get('shipping_courier')
        
        if not shipping_cost or not shipping_courier:
            return Response(
                {"detail": "Shipping cost and courier are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update order
        order.shipping_cost = shipping_cost
        order.shipping_courier = shipping_courier
        order.save()
        
        return Response({"detail": "Shipping cost updated successfully"})


class ShippingRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingRate.objects.all()
    serializer_class = ShippingRateSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CalculateShippingView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShippingCostRequestSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            api_key = getattr(settings, 'RAJAONGKIR_API_KEY', None)
            if not api_key:
                return Response(
                    {"detail": "RajaOngkir API key not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            url = "https://rajaongkir.komerce.id/api/v1/calculate/domestic-cost"
            headers = {
                'key': api_key,
                'content-type': "application/x-www-form-urlencoded"
            }
            
            # Prepare payload as form data
            payload = {
                'origin': serializer.validated_data['origin_city'],
                'destination': serializer.validated_data['destination_city'],
                'weight': serializer.validated_data['weight'],
                'courier': serializer.validated_data['courier']
            }
            
            try:
                # Make request to RajaOngkir API with form-urlencoded data
                response = requests.post(url, headers=headers, data=payload)
                
                # Log the entire response for debugging
                print("RajaOngkir Response Status:", response.status_code)
                print("RajaOngkir Response Headers:", response.headers)
                print("RajaOngkir Response Content:", response.text)

                try:
                    # Try to parse JSON response
                    raw_data = response.json()
                    return Response(raw_data)
                except ValueError:
                    # If not JSON, return the raw text
                    return Response(
                        {"raw_response": response.text, "status_code": response.status_code}
                    )
                
            except requests.exceptions.RequestException as e:
                return Response(
                    {"detail": f"Error connecting to RajaOngkir API: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status != 'pending':
            return Response(
                {"detail": f"Cannot process payment for order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        server_key = getattr(settings, 'MIDTRANS_SERVER_KEY', '').strip()
        if not server_key:
            return Response(
                {"detail": "Midtrans API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        env = getattr(settings, 'MIDTRANS_ENV', 'production')
        api_url = "https://app.midtrans.com/snap/v1/transactions" \
            if env == 'production' else "https://app.sandbox.midtrans.com/snap/v1/transactions"

        transaction_id = f"{order.id}-{uuid.uuid4().hex[:8]}"
        transaction_details = {
            "order_id": transaction_id,
            "gross_amount": int(order.final_price),
        }

        name_parts = order.shipping_name.strip().split(' ')
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        customer_details = {
            "first_name": first_name,
            "last_name": last_name,
            "email": order.user.email,
            "phone": order.shipping_phone,
            "billing_address": {
                "first_name": first_name,
                "last_name": last_name,
                "email": order.user.email,
                "phone": order.shipping_phone,
                "address": order.shipping_address,
                "city": order.shipping_city,
                "postal_code": order.shipping_postal_code,
                "country_code": "IDN"
            },
            "shipping_address": {
                "first_name": first_name,
                "last_name": last_name,
                "email": order.user.email,
                "phone": order.shipping_phone,
                "address": order.shipping_address,
                "city": order.shipping_city,
                "postal_code": order.shipping_postal_code,
                "country_code": "IDN"
            }
        }

        item_details = []
        for item in order.items.all():
            item_details.append({
                "id": f"ITEM-{item.id}",
                "price": int(item.price),
                "quantity": item.quantity,
                "name": f"{item.product_name} - {item.variant_name}"
            })

        if order.shipping_cost > 0:
            item_details.append({
                "id": f"SHIPPING-{order.id}",
                "price": int(order.shipping_cost),
                "quantity": 1,
                "name": f"Shipping Cost ({order.shipping_courier})"
            })

        if order.discount > 0:
            item_details.append({
                "id": f"DISCOUNT-{order.id}",
                "price": -int(order.discount),
                "quantity": 1,
                "name": "Discount"
            })

        payload = {
            "transaction_details": transaction_details,
            "customer_details": customer_details,
            "item_details": item_details
        }

        try:
            response = self.create_midtrans_transaction(api_url, server_key, payload)
            result = response.json()

            if response.status_code != 201 or "token" not in result:
                logging.error(f"Midtrans error response: {result}")
                return Response(
                    {"detail": result.get("status_message", "Midtrans API error")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            PaymentTransaction.objects.create(
                order=order,
                transaction_id=transaction_id,
                payment_type="Midtrans",
                amount=order.final_price,
                status="pending",
                transaction_time=timezone.now(),
                transaction_status="pending",
                raw_response=result
            )

            return Response({
                "token": result["token"],
                "redirect_url": result["redirect_url"]
            })

        except requests.exceptions.RequestException as e:
            logging.exception("Error connecting to Midtrans API")
            return Response(
                {"detail": f"Connection error: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logging.exception("Unexpected error during payment processing")
            return Response(
                {"detail": f"Unexpected error: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create_midtrans_transaction(self, api_url, server_key, payload):
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_string}"
        }
        return requests.post(api_url, headers=headers, json=payload)



class PaymentNotificationView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        # Get notification data from Midtrans
        notification_data = request.data
        
        # Verify transaction status
        transaction_id = notification_data.get('order_id')
        transaction_status = notification_data.get('transaction_status')
        fraud_status = notification_data.get('fraud_status', None)
        
        # Find payment transaction
        try:
            payment = PaymentTransaction.objects.get(transaction_id=transaction_id)
            order = payment.order
            
            # Update payment data
            payment.transaction_status = transaction_status
            payment.fraud_status = fraud_status
            payment.raw_response = notification_data
            
            # Set status based on transaction_status and fraud_status
            if transaction_status == 'capture':
                if fraud_status == 'accept':
                    payment.status = 'success'
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                else:
                    payment.status = 'failed'
            elif transaction_status == 'settlement':
                payment.status = 'success'
                order.status = 'paid'
                order.paid_at = timezone.now()
            elif transaction_status == 'deny' or transaction_status == 'cancel' or transaction_status == 'expire':
                payment.status = 'failed'
            elif transaction_status == 'pending':
                payment.status = 'pending'
            
            payment.save()
            order.save()
            
            return Response({"status": "OK"})
        
        except PaymentTransaction.DoesNotExist:
            return Response(
                {"detail": "Payment transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )