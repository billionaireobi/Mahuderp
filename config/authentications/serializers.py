"""
Authentication Serializers for Mahad Group Accounting Suite
File: apps/auth/serializers.py

This module contains all serializers for user authentication, registration,
password management, and user profile operations.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import User, LoginHistory, RefreshToken
import re


class UserSerializer(serializers.ModelSerializer):
    """
    Basic User Serializer
    Used for displaying user information in responses
    """
    
    full_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'company', 'company_name', 'branch', 'branch_name',
            'is_active', 'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    """
    User Registration Serializer
    Handles new user registration with validation
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters with letters, numbers, and special characters"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Re-enter your password for confirmation"
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'role', 'company', 'branch'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email format and uniqueness"""
        # Check email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Invalid email format")
        
        # Check if email already exists (case-insensitive)
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        return value.lower()
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if value:
            # Remove spaces and special characters
            cleaned_phone = re.sub(r'[^\d+]', '', value)
            if len(cleaned_phone) < 10:
                raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation and role-based requirements"""
        # Check password match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match"
            })
        
        # Validate role-based company/branch requirements
        role = attrs.get('role')
        company = attrs.get('company')
        branch = attrs.get('branch')
        
        if role == 'HQ_ADMIN':
            # HQ Admin should not have company/branch
            if company or branch:
                raise serializers.ValidationError({
                    "role": "HQ Admin should not be assigned to a company or branch"
                })
        else:
            # Other roles must have a company
            if not company:
                raise serializers.ValidationError({
                    "company": "This role requires a company assignment"
                })
            
            # Branch user must have a branch
            if role == 'BRANCH_USER' and not branch:
                raise serializers.ValidationError({
                    "branch": "Branch User must be assigned to a branch"
                })
            
            # Validate branch belongs to company
            if branch and branch.company != company:
                raise serializers.ValidationError({
                    "branch": "Branch must belong to the selected company"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    User Login Serializer
    Handles user authentication with email and password
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="User's email address"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="User's password"
    )
    device_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional device name for tracking sessions"
    )
    
    def validate(self, attrs):
        """Validate credentials and check account status"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Email and password are required")
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        # Check if account is locked
        if user.is_locked:
            minutes_left = int((user.account_locked_until - timezone.now()).total_seconds() / 60)
            if minutes_left > 0:
                raise serializers.ValidationError(
                    f"Account is locked due to multiple failed login attempts. "
                    f"Please try again in {minutes_left} minute{'s' if minutes_left != 1 else ''}."
                )
            else:
                # Lock expired, unlock account
                user.unlock_account()
        
        # Check if account is active
        if not user.is_active:
            raise serializers.ValidationError(
                "This account has been deactivated. Please contact support."
            )
        
        # Authenticate user
        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not authenticated_user:
            # Record failed login attempt
            try:
                user_obj = User.objects.get(email=email)
                user_obj.record_failed_login()
            except User.DoesNotExist:
                pass
            
            raise serializers.ValidationError("Invalid email or password")
        
        attrs['user'] = authenticated_user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Change Password Serializer
    Handles password change for authenticated users
    """
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="New password"
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )
    
    def validate_old_password(self, value):
        """Validate old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation and requirements"""
        # Check new passwords match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "New password fields didn't match"
            })
        
        # Ensure new password is different from old
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                "new_password": "New password must be different from old password"
            })
        
        return attrs
    
    def save(self):
        """Update user password and revoke all sessions"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.password_changed_at = timezone.now()
        user.force_password_change = False
        user.save(update_fields=['password', 'password_changed_at', 'force_password_change'])
        
        # Revoke all existing refresh tokens for security
        RefreshToken.objects.filter(user=user, is_revoked=False).update(
            is_revoked=True,
            revoked_at=timezone.now()
        )
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password Reset Request Serializer
    Handles password reset email requests
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="Email address associated with the account"
    )
    
    def validate_email(self, value):
        """Validate email (don't reveal if it exists for security)"""
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password Reset Confirm Serializer
    Handles password reset with token
    """
    
    token = serializers.CharField(
        required=True,
        help_text="Password reset token from email"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="New password"
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )
    
    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Password fields didn't match"
            })
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """
    Refresh Token Serializer
    Handles access token refresh
    """
    
    refresh_token = serializers.CharField(
        required=True,
        help_text="Refresh token received during login"
    )


class LogoutSerializer(serializers.Serializer):
    """
    Logout Serializer
    Handles user logout
    """
    
    refresh_token = serializers.CharField(
        required=True,
        help_text="Refresh token to revoke"
    )


class EmailVerificationSerializer(serializers.Serializer):
    """
    Email Verification Serializer
    Handles email verification with token
    """
    
    token = serializers.CharField(
        required=True,
        help_text="Email verification token"
    )


class LoginHistorySerializer(serializers.ModelSerializer):
    """
    Login History Serializer
    Displays user login history
    """
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'email_attempted', 'status', 'failure_reason',
            'ip_address', 'user_agent', 'country', 'city', 'timestamp'
        ]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User Profile Serializer
    Detailed user profile with permissions and company details
    """
    
    full_name = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()
    branch_details = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'company', 'company_details',
            'branch', 'branch_details', 'is_active', 'is_verified',
            'date_joined', 'last_login', 'last_activity', 'permissions'
        ]
        read_only_fields = ['id', 'email', 'role', 'company', 'branch', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()
    
    def get_company_details(self, obj):
        """Get company details if assigned"""
        if obj.company:
            return {
                'id': str(obj.company.id),
                'name': obj.company.name,
                'code': obj.company.code,
                'country': obj.company.country
            }
        return None
    
    def get_branch_details(self, obj):
        """Get branch details if assigned"""
        if obj.branch:
            return {
                'id': str(obj.branch.id),
                'name': obj.branch.name,
                'code': obj.branch.code
            }
        return None
    
    def get_permissions(self, obj):
        """Return role-based permissions"""
        permissions_map = {
            'HQ_ADMIN': [
                'view_all_companies',
                'manage_users',
                'system_configuration',
                'view_consolidated_reports',
                'manage_all_data',
                'create_companies',
                'delete_companies'
            ],
            'COUNTRY_MANAGER': [
                'view_company_data',
                'manage_company_operations',
                'approve_transactions',
                'view_company_reports',
                'manage_branches',
                'manage_employers',
                'manage_job_orders'
            ],
            'FINANCE_MANAGER': [
                'manage_invoices',
                'manage_bills',
                'manage_payments',
                'approve_payments',
                'period_close',
                'view_financial_reports',
                'bank_reconciliation',
                'manage_receipts'
            ],
            'ACCOUNTANT': [
                'create_invoices',
                'create_bills',
                'record_receipts',
                'record_payments',
                'view_reports',
                'manage_candidates',
                'view_job_orders'
            ],
            'BRANCH_USER': [
                'manage_candidates',
                'view_job_orders',
                'limited_financial_access',
                'create_candidate_costs'
            ],
            'AUDITOR': [
                'view_all_data',
                'download_reports',
                'view_audit_logs',
                'view_financial_reports'
            ]
        }
        return permissions_map.get(obj.role, [])


class ActiveSessionSerializer(serializers.ModelSerializer):
    """
    Active Session Serializer
    Displays user's active sessions
    """
    
    class Meta:
        model = RefreshToken
        fields = [
            'id', 'device_name', 'ip_address', 'user_agent',
            'created_at', 'last_used_at', 'expires_at'
        ]
        read_only_fields = fields