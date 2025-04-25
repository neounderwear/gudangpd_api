from rest_framework import permissions
import os

class APISecretPermission(permissions.BasePermission):
    """
    Permission that requires a valid API secret for administrative endpoints.
    Used for very sensitive operations like manually triggering payment notifications.
    """
    
    def has_permission(self, request, view):
        # Get API secret from settings
        api_secret = os.environ.get('API_SECRET_KEY')
        
        # Check header
        secret_header = request.META.get('HTTP_X_API_SECRET')
        
        # If API secret is not configured or doesn't match header, deny access
        if not api_secret or secret_header != api_secret:
            return False
        
        return True