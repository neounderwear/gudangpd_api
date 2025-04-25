import secrets
import string
from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .serializers import (
    UserSerializer, UserRegisterSerializer, ChangePasswordSerializer,
    ResetPasswordEmailSerializer, ResetPasswordSerializer, APIKeySerializer
)
from .models import APIKey

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        # Regular users can only see their own profile
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], serializer_class=ChangePasswordSerializer)
    def change_password(self, request):
        """Change password for current user"""
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response({"old_password": ["Wrong password."]}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Set the new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            # Update session
            update_session_auth_hash(request, user)
            return Response({"message": "Password updated successfully."}, 
                           status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)


class ResetPasswordEmailView(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailSerializer
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Create password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build password reset link (frontend URL)
                reset_url = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
                
                # Send email
                mail_subject = 'Reset your password'
                message = f'Please click the following link to reset your password: {reset_url}'
                send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [email])
                
                return Response(
                    {"message": "Password reset email has been sent."},
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist for security
                pass
                
        return Response(
            {"message": "Password reset email has been sent if account exists."},
            status=status.HTTP_200_OK
        )


class ResetPasswordConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, uidb64, token):
        try:
            # Decode the UID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Verify token
            if default_token_generator.check_token(user, token):
                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid():
                    # Set new password
                    user.set_password(serializer.validated_data['password'])
                    user.save()
                    return Response(
                        {"message": "Password has been reset successfully."},
                        status=status.HTTP_200_OK
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"error": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid token or user."},
                status=status.HTTP_400_BAD_REQUEST
            )


class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key"""
        api_key = self.get_object()
        
        # Generate a new random API key
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Update API key
        api_key.key = key
        api_key.save()
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)