"""
URL Configuration for Mahad Group Accounting Suite
File: config/urls.py

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from django.http import JsonResponse

# OpenAPI / Swagger views (drf-spectacular)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Welcome to Mahad Group Accounting API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'auth': '/api/auth/',
            'core': '/api/',
            'dashboard': '/api/dashboard/stats/',
            'companies': '/api/companies/',
            'employers': '/api/employers/',
            'vendors': '/api/vendors/',
            'job_orders': '/api/job-orders/',
            'candidates': '/api/candidates/',
            'invoices': '/api/invoices/',
        },
        'documentation': '/api/docs/',
    })


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Root
    path('', api_root, name='api-root'),
    
    # Authentication endpoints
    path('api/auth/', include('authentications.urls')),
    
    # Core API endpoints (will be added later)
    path('api/core/', include('core.urls')),
    # Dashboard endpoints
    path('api/dashboard/', include('dashboards.urls')),
    # OpenAPI Schema and documentation
    # OpenAPI Schema and documentation
    # - /api/schema/  -> raw OpenAPI JSON/YAML
    # - /api/docs/    -> Swagger UI (interactive)
    # - /api/redoc/   -> ReDoc UI
    # Note: These are registered using drf-spectacular. In production you may want
    # to restrict access to these endpoints or disable them when DEBUG=False.
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    # Swagger UI (interactive)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),
    # ReDoc UI
    path('api/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar (import dynamically to avoid static import errors)
    try:
        import importlib
        debug_toolbar = importlib.import_module('debug_toolbar')
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        # debug_toolbar is optional in development; ignore if not installed
        pass

# Custom error handlers (optional)
# handler404 = 'config.views.handler404'
# handler500 = 'config.views.handler500'