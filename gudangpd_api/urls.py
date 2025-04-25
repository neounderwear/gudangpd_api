"""
URL configuration for gudangpd_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import APIDocsHomeView, APIGuideView
from .health import health_check

# Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="Gudang Pakaian Dalam API",
        default_version="v1",
        description="""
        API untuk layanan e-commerce dengan fitur:
        
        1. Manajemen produk (CRUD)
        2. Autentikasi akun pengguna (register, login, reset password)
        3. Proses pemesanan produk oleh pembeli
        4. Menghitung biaya ongkos kirim (RajaOngkir)
        5. Pembayaran (Midtrans)
        6. Fitur keamanan API Key
        
        ### Autentikasi
        API ini mendukung dua metode autentikasi:
        
        1. JWT Token (Bearer token) - Untuk aplikasi web/mobile
        2. API Key (X-API-Key header) - Untuk integrasi dengan layanan lain
        
        ### Dokumentasi
        Untuk detail lengkap, silakan lihat dokumentasi di bawah ini.
        """,
        contact=openapi.Contact(email="neounderwearshop@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('products.urls')),
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/', include('orders.urls')),
    
    # Swagger
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/v1/docs/', APIDocsHomeView.as_view(), name='api-docs-home'),
    path('api/v1/guide/', APIGuideView.as_view(), name='api-guide'),
    
    path('health/', health_check, name='health-check'),
]

# Serving media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)