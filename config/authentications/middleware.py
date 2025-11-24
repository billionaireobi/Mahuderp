"""
Custom Authentication Middleware for Mahad Group Accounting Suite
File: apps/auth/middleware.py

This module contains custom middleware for tracking user activity,
handling JWT authentication, and enforcing security policies.
"""
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class UserActivityMiddleware:
    """
    Middleware to track user activity
    Updates last_activity timestamp on each request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Update last activity for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Update only if it's been more than 5 minutes since last update
            # This prevents excessive database writes
            if not request.user.last_activity or \
               (timezone.now() - request.user.last_activity).total_seconds() > 300:
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])
        
        return response


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users via JWT token
    Adds user to request object if valid token is present
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Try to authenticate using JWT
        jwt_auth = JWTAuthentication()
        
        try:
            # Get token from header
            header = jwt_auth.get_header(request)
            if header:
                raw_token = jwt_auth.get_raw_token(header)
                validated_token = jwt_auth.get_validated_token(raw_token)
                user = jwt_auth.get_user(validated_token)
                
                # Add user to request
                request.user = user
            else:
                request.user = AnonymousUser()
        except (InvalidToken, TokenError):
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response


class AccountLockoutMiddleware:
    """
    Middleware to check if user account is locked
    Prevents locked users from accessing the system
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if account is locked
            if request.user.is_locked:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Account is locked',
                    'message': 'Your account has been locked due to multiple failed login attempts. Please try again later.'
                }, status=403)
            
            # Check if user is inactive
            if not request.user.is_active:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Account is inactive',
                    'message': 'Your account has been deactivated. Please contact support.'
                }, status=403)
        
        response = self.get_response(request)
        return response


class ForcePasswordChangeMiddleware:
    """
    Middleware to force password change if required
    Redirects users who need to change their password
    """
    
    # List of URLs that don't require password change
    EXEMPT_URLS = [
        '/api/auth/change-password/',
        '/api/auth/logout/',
        '/api/auth/profile/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if user needs to change password
            if request.user.force_password_change:
                # Check if current URL is exempt
                if not any(request.path.startswith(url) for url in self.EXEMPT_URLS):
                    from django.http import JsonResponse
                    return JsonResponse({
                        'error': 'Password change required',
                        'message': 'You must change your password before accessing this resource.',
                        'action_required': 'change_password'
                    }, status=403)
        
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Only add HSTS in production
        if not request.get_host().startswith('localhost'):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log API requests for auditing
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log request (you can customize this to save to database)
        if hasattr(request, 'user') and request.user.is_authenticated:
            print(f"[{timezone.now()}] {request.method} {request.path} - User: {request.user.email}")
        
        response = self.get_response(request)
        return response


class EmailVerificationMiddleware:
    """
    Middleware to check if user's email is verified
    Can be configured to block unverified users from certain endpoints
    """
    
    # List of URLs that don't require email verification
    EXEMPT_URLS = [
        '/api/auth/verify-email/',
        '/api/auth/resend-verification/',
        '/api/auth/logout/',
        '/api/auth/profile/',
    ]
    
    # Set to True to enforce email verification
    ENFORCE_VERIFICATION = False  # Change to True to enforce
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if self.ENFORCE_VERIFICATION:
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Check if user's email is verified
                if not request.user.is_verified:
                    # Check if current URL is exempt
                    if not any(request.path.startswith(url) for url in self.EXEMPT_URLS):
                        from django.http import JsonResponse
                        return JsonResponse({
                            'error': 'Email verification required',
                            'message': 'Please verify your email address to access this resource.',
                            'action_required': 'verify_email'
                        }, status=403)
        
        response = self.get_response(request)
        return response