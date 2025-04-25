from django.utils.deprecation import MiddlewareMixin

class CSRFExemptMiddleware(MiddlewareMixin):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Jika URL dimulai dengan /api/, lewati CSRF check
        if request.path.startswith('/api/'):
            # Set tanda bahwa request ini tidak perlu CSRF check
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None