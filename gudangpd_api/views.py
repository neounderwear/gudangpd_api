from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class APIDocsHomeView(TemplateView):
    """
    Custom view for API documentation home page
    """
    template_name = 'api_docs/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Gudang Pakaian Dalam API Documentation'
        context['api_version'] = 'v1'
        context['sections'] = [
            {
                'name': 'Products API',
                'description': 'Manage products, categories, brands, and variants',
                'endpoints': [
                    {'path': '/api/v1/products/', 'method': 'GET, POST', 'description': 'List and create products'},
                    {'path': '/api/v1/products/{id}/', 'method': 'GET, PUT, DELETE', 'description': 'Retrieve, update or delete a product'},
                    {'path': '/api/v1/categories/', 'method': 'GET, POST', 'description': 'List and create categories'},
                    {'path': '/api/v1/brands/', 'method': 'GET, POST', 'description': 'List and create brands'},
                    {'path': '/api/v1/product-variants/', 'method': 'GET, POST', 'description': 'List and create product variants'},
                ]
            },
            {
                'name': 'Authentication API',
                'description': 'User registration, login, and password management',
                'endpoints': [
                    {'path': '/api/v1/auth/register/', 'method': 'POST', 'description': 'Register a new user'},
                    {'path': '/api/v1/auth/login/', 'method': 'POST', 'description': 'Login and get JWT token'},
                    {'path': '/api/v1/auth/token/refresh/', 'method': 'POST', 'description': 'Refresh JWT token'},
                    {'path': '/api/v1/auth/reset-password/', 'method': 'POST', 'description': 'Request password reset'},
                    {'path': '/api/v1/auth/api-keys/', 'method': 'GET, POST', 'description': 'Manage API keys'},
                ]
            },
            {
                'name': 'Orders API',
                'description': 'Process orders, shipping, and payments',
                'endpoints': [
                    {'path': '/api/v1/orders/', 'method': 'GET, POST', 'description': 'List and create orders'},
                    {'path': '/api/v1/orders/{id}/', 'method': 'GET', 'description': 'Retrieve order details'},
                    {'path': '/api/v1/orders/{id}/cancel/', 'method': 'POST', 'description': 'Cancel an order'},
                    {'path': '/api/v1/calculate-shipping/', 'method': 'POST', 'description': 'Calculate shipping cost'},
                    {'path': '/api/v1/orders/{id}/create-payment/', 'method': 'POST', 'description': 'Create payment for order'},
                ]
            }
        ]
        return context


class APIGuideView(LoginRequiredMixin, TemplateView):
    """
    Custom view for API integration guide (requires login)
    """
    template_name = 'api_docs/guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'API Integration Guide'
        return context