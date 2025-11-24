"""
Authentication Views for Mahad Group Accounting Suite
File: apps/auth/views.py

This module contains all API views for user authentication, registration,
password management, and session management using function-based views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import secrets

from .models import User, RefreshToken, LoginHistory, PasswordResetToken, EmailVerificationToken
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, RefreshTokenSerializer,
    LogoutSerializer, LoginHistorySerializer, UserProfileSerializer,
    ActiveSessionSerializer, EmailVerificationSerializer
)
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from .utils import (
    get_client_ip, get_user_agent, parse_user_agent,
    send_password_reset_email, send_verification_email,
    send_password_changed_notification
)


@extend_schema(request=RegisterSerializer, responses=UserSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    User Registration
    
    POST /api/auth/register/
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "role": "ACCOUNTANT",
        "company": "uuid-here",
        "branch": "uuid-here"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user
    user = serializer.save()
    
    # Create email verification token
    token = secrets.token_urlsafe(32)
    verification_token = EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24)
    )
    
    # Send verification email
    try:
        send_verification_email(user, token)
    except Exception as e:
        print(f"Failed to send verification email: {e}")
    
    return Response({
        'message': 'Registration successful. Please check your email to verify your account.',
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


@extend_schema(request=LoginSerializer, responses=UserSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User Login
    
    POST /api/auth/login/
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "device_name": "Chrome on Windows"  // optional
    }
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        # Record failed login in history
        email = request.data.get('email', '').lower()
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        LoginHistory.objects.create(
            user=None,
            email_attempted=email,
            status='FAILED',
            failure_reason=str(serializer.errors),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response({
            'error': 'Login failed',
            'details': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user = serializer.validated_data['user']
    device_name = serializer.validated_data.get('device_name', 'Unknown Device')
    
    # Record successful login
    user.record_successful_login()
    
    # Create JWT tokens
    jwt_refresh = JWTRefreshToken.for_user(user)
    access_token = str(jwt_refresh.access_token)
    refresh_token_str = str(jwt_refresh)
    
    # Store refresh token in database
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    refresh_token = RefreshToken.objects.create(
        user=user,
        token=refresh_token_str,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=timezone.now() + timedelta(days=7)
    )
    
    # Record login history
    LoginHistory.objects.create(
        user=user,
        email_attempted=user.email,
        status='SUCCESS',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return Response({
        'message': 'Login successful',
        'access': access_token,
        'refresh': refresh_token_str,
        'user': UserSerializer(user).data,
        'expires_in': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    }, status=status.HTTP_200_OK)


@extend_schema(request=LogoutSerializer, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User Logout
    
    POST /api/auth/logout/
    
    Request Body:
    {
        "refresh_token": "your_refresh_token"
    }
    """
    serializer = LogoutSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    refresh_token_str = serializer.validated_data['refresh_token']
    
    try:
        # Find and revoke refresh token
        refresh_token = RefreshToken.objects.get(
            token=refresh_token_str,
            user=request.user,
            is_revoked=False
        )
        refresh_token.revoke()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except RefreshToken.DoesNotExist:
        return Response({
            'error': 'Invalid or already revoked token'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, responses=OpenApiTypes.NONE)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_all(request):
    """
    Logout from all devices
    
    POST /api/auth/logout-all/
    """
    # Revoke all refresh tokens for user
    count = RefreshToken.objects.filter(
        user=request.user,
        is_revoked=False
    ).update(
        is_revoked=True,
        revoked_at=timezone.now()
    )
    
    return Response({
        'message': f'Logged out from all devices successfully',
        'sessions_revoked': count
    }, status=status.HTTP_200_OK)


@extend_schema(request=RefreshTokenSerializer, responses=None)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh Access Token
    
    POST /api/auth/refresh/
    
    Request Body:
    {
        "refresh_token": "your_refresh_token"
    }
    """
    serializer = RefreshTokenSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    refresh_token_str = serializer.validated_data['refresh_token']
    
    try:
        # Validate refresh token
        refresh_token = RefreshToken.objects.get(token=refresh_token_str)
        
        if not refresh_token.is_valid:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Create new access token
        jwt_refresh = JWTRefreshToken(refresh_token_str)
        access_token = str(jwt_refresh.access_token)
        
        # Update last used timestamp
        refresh_token.last_used_at = timezone.now()
        refresh_token.save(update_fields=['last_used_at'])
        
        return Response({
            'access': access_token,
            'expires_in': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        }, status=status.HTTP_200_OK)
        
    except RefreshToken.DoesNotExist:
        return Response({
            'error': 'Invalid refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'error': 'Token refresh failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ChangePasswordSerializer, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change Password
    
    POST /api/auth/change-password/
    
    Request Body:
    {
        "old_password": "OldPass123!",
        "new_password": "NewPass123!",
        "new_password_confirm": "NewPass123!"
    }
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Save new password
    user = serializer.save()
    
    # Send notification email
    try:
        send_password_changed_notification(user)
    except Exception as e:
        print(f"Failed to send password change notification: {e}")
    
    return Response({
        'message': 'Password changed successfully. Please login again with your new password.'
    }, status=status.HTTP_200_OK)


@extend_schema(request=PasswordResetRequestSerializer, responses=None)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request Password Reset
    
    POST /api/auth/password-reset/
    
    Request Body:
    {
        "email": "user@example.com"
    }
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        # Create reset token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1),
            ip_address=get_client_ip(request)
        )
        
        # Send reset email
        send_password_reset_email(user, token)
        
    except User.DoesNotExist:
        # Don't reveal if email exists (security best practice)
        pass
    
    return Response({
        'message': 'If an account exists with this email, a password reset link has been sent.'
    }, status=status.HTTP_200_OK)


@extend_schema(request=PasswordResetConfirmSerializer, responses=None)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm Password Reset
    
    POST /api/auth/password-reset/confirm/
    
    Request Body:
    {
        "token": "reset_token_from_email",
        "new_password": "NewPass123!",
        "new_password_confirm": "NewPass123!"
    }
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid:
            return Response({
                'error': 'Invalid or expired reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update password
        user = reset_token.user
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.save(update_fields=['password', 'password_changed_at'])
        
        # Mark token as used
        reset_token.mark_as_used()
        
        # Revoke all existing refresh tokens for security
        RefreshToken.objects.filter(user=user, is_revoked=False).update(
            is_revoked=True,
            revoked_at=timezone.now()
        )
        
        # Send notification
        try:
            send_password_changed_notification(user)
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        return Response({
            'message': 'Password reset successful. Please login with your new password.'
        }, status=status.HTTP_200_OK)
        
    except PasswordResetToken.DoesNotExist:
        return Response({
            'error': 'Invalid reset token'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=EmailVerificationSerializer, responses=None)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify Email Address
    
    POST /api/auth/verify-email/
    
    Request Body:
    {
        "token": "verification_token_from_email"
    }
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            'error': 'Token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if not verification_token.is_valid:
            return Response({
                'error': 'Invalid or expired verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark user as verified
        user = verification_token.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        
        # Mark token as used
        verification_token.mark_as_used()
        
        return Response({
            'message': 'Email verified successfully. You can now login.'
        }, status=status.HTTP_200_OK)
        
    except EmailVerificationToken.DoesNotExist:
        return Response({
            'error': 'Invalid verification token'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=UserProfileSerializer, responses=UserProfileSerializer)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or Update User Profile
    
    GET /api/auth/profile/
    PATCH /api/auth/profile/
    
    PATCH Request Body:
    {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890"
    }
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(responses=LoginHistorySerializer(many=True))
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def login_history(request):
    """
    Get User Login History
    
    GET /api/auth/login-history/
    
    Query Parameters:
    - limit: Number of records to return (default: 20, max: 100)
    """
    limit = request.query_params.get('limit', 20)
    try:
        limit = min(int(limit), 100)  # Max 100 records
    except (ValueError, TypeError):
        limit = 20
    
    history = LoginHistory.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:limit]
    
    serializer = LoginHistorySerializer(history, many=True)
    
    return Response({
        'history': serializer.data,
        'total': history.count()
    }, status=status.HTTP_200_OK)


@extend_schema(responses=ActiveSessionSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_sessions(request):
    """
    Get Active Sessions
    
    GET /api/auth/sessions/
    """
    sessions = RefreshToken.objects.filter(
        user=request.user,
        is_revoked=False,
        expires_at__gt=timezone.now()
    ).order_by('-last_used_at')
    
    serializer = ActiveSessionSerializer(sessions, many=True)
    
    return Response({
        'sessions': serializer.data,
        'total': sessions.count()
    }, status=status.HTTP_200_OK)


@extend_schema(responses=None)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_session(request, session_id):
    """
    Revoke a Specific Session
    
    DELETE /api/auth/sessions/{session_id}/
    """
    try:
        session = RefreshToken.objects.get(
            id=session_id,
            user=request.user,
            is_revoked=False
        )
        session.revoke()
        
        return Response({
            'message': 'Session revoked successfully'
        }, status=status.HTTP_200_OK)
        
    except RefreshToken.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend Email Verification
    
    POST /api/auth/resend-verification/
    
    Request Body:
    {
        "email": "user@example.com"
    }
    """
    email = request.data.get('email', '').lower()
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        if user.is_verified:
            return Response({
                'message': 'Email is already verified'
            }, status=status.HTTP_200_OK)
        
        # Invalidate old tokens
        EmailVerificationToken.objects.filter(
            user=user,
            is_used=False
        ).update(is_used=True, used_at=timezone.now())
        
        # Create new token
        token = secrets.token_urlsafe(32)
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Send email
        send_verification_email(user, token)
        
    except User.DoesNotExist:
        # Don't reveal if email exists
        pass
    
    return Response({
        'message': 'If an account exists with this email, a verification link has been sent.'
    }, status=status.HTTP_200_OK)


@extend_schema(responses=UserSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    """
    Check Authentication Status
    
    GET /api/auth/check/
    
    Returns current user information if authenticated
    """
    serializer = UserSerializer(request.user)
    return Response({
        'authenticated': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)