from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .models import APIKey

class APIKeyMiddleware:
    """
    Middleware to check for a valid API key in request headers.
    This is a second layer of security in addition to JWT authentication.
    Public routes are excluded from API key checking.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Compile a list of URLs that don't require API key
        self.public_urls = getattr(settings, 'API_KEY_EXEMPT_URLS', [
            '/admin/', 
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/auth/token/refresh/',
            '/api/v1/auth/reset-password/',
            '/api/v1/payment-notification/',
            '/',
            '/redoc/',
        ])
    
    def __call__(self, request):
        # Skip API key check for public URLs
        path = request.path_info
        if any(path.startswith(url) for url in self.public_urls):
            return self.get_response(request)
        
        # Check for API key in header
        api_key = request.META.get('HTTP_X_API_KEY')
        
        # If API key is not provided, proceed to let DRF handle authentication
        # This allows using either API key or JWT token
        if not api_key:
            return self.get_response(request)
        
        try:
            # Find and validate API key
            key = APIKey.objects.get(key=api_key, is_active=True)
            
            # Update last used timestamp
            key.last_used_at = timezone.now()
            key.save(update_fields=['last_used_at'])
            
            # Add user to request for downstream processing
            request.user = key.user
            
        except APIKey.DoesNotExist:
            return JsonResponse({'detail': 'Invalid API key'}, status=401)
        
        return self.get_response(request)