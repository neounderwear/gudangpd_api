from rest_framework import authentication
from rest_framework import exceptions
from django.utils import timezone
from .models import APIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication using API key from header.
    """
    def authenticate(self, request):
        # Get API key from header
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return None
        
        try:
            # Find the API key in database
            key = APIKey.objects.get(key=api_key, is_active=True)
            
            # Update last used timestamp
            key.last_used_at = timezone.now()
            key.save(update_fields=['last_used_at'])
            
            # Return authenticated user
            return key.user, None
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')