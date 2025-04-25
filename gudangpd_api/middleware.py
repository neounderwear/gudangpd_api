import time
import json
import logging
from django.utils import timezone

# Create a logger
logger = logging.getLogger('api_request')

class APIRequestLogMiddleware:
    """
    Middleware to log all API requests for security auditing.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip logging for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Mark start time
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate time taken
        duration = time.time() - start_time
        
        # Extract request info
        request_data = {
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'duration': duration,
            'timestamp': timezone.now().isoformat(),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Log request
        logger.info(json.dumps(request_data))
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip