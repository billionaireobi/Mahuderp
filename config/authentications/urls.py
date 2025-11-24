"""
Authentication URLs for Mahad Group Accounting Suite
File: apps/auth/urls.py

This module defines all URL patterns for authentication endpoints.
"""
from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # ============================================================
    # REGISTRATION & EMAIL VERIFICATION
    # ============================================================
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.resend_verification_email, name='resend-verification'),
    
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('logout-all/', views.logout_all, name='logout-all'),
    path('refresh/', views.refresh_token, name='refresh-token'),
    path('check/', views.check_auth, name='check-auth'),
    
    # ============================================================
    # PASSWORD MANAGEMENT
    # ============================================================
    path('change-password/', views.change_password, name='change-password'),
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    
    # ============================================================
    # USER PROFILE
    # ============================================================
    path('profile/', views.user_profile, name='profile'),
    
    # ============================================================
    # SECURITY & SESSION MANAGEMENT
    # ============================================================
    path('login-history/', views.login_history, name='login-history'),
    path('sessions/', views.active_sessions, name='active-sessions'),
    path('sessions/<uuid:session_id>/', views.revoke_session, name='revoke-session'),
]