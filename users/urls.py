from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import (
    UserViewSet, RegisterView, ResetPasswordEmailView, 
    ResetPasswordConfirmView, APIKeyViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'api-keys', APIKeyViewSet, basename='api-keys')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Password reset
    path('reset-password/', ResetPasswordEmailView.as_view(), name='password_reset'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
]