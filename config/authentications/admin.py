"""
Django Admin Configuration for Authentication
File: apps/auth/admin.py
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, RefreshToken, LoginHistory, PasswordResetToken, EmailVerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    
    list_display = [
        'email', 'full_name_display', 'role', 'company_display', 'branch_display',
        'is_active', 'is_verified', 'status_badge', 'date_joined'
    ]
    list_filter = ['role', 'is_active', 'is_verified', 'company', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone')
        }),
        ('Role & Assignment', {
            'fields': ('role', 'company', 'branch')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
        ('Security', {
            'fields': (
                'password',
                'failed_login_attempts',
                'last_failed_login',
                'account_locked_until',
                'password_changed_at',
                'force_password_change'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login', 'last_activity', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Account Information', {
            'fields': ('email', 'password1', 'password2')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('Role & Assignment', {
            'fields': ('role', 'company', 'branch')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'last_activity', 'updated_at', 'password_changed_at']
    
    def full_name_display(self, obj):
        """Display full name"""
        return obj.get_full_name()
    full_name_display.short_description = 'Full Name'
    
    def company_display(self, obj):
        """Display company name"""
        return obj.company.name if obj.company else '-'
    company_display.short_description = 'Company'
    
    def branch_display(self, obj):
        """Display branch name"""
        return obj.branch.name if obj.branch else '-'
    branch_display.short_description = 'Branch'
    
    def status_badge(self, obj):
        """Display account status with color coding"""
        if obj.is_locked:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">🔒 LOCKED</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">⛔ INACTIVE</span>'
            )
        elif not obj.is_verified:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 3px 10px; '
                'border-radius: 3px;">📧 UNVERIFIED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✅ ACTIVE</span>'
            )
    status_badge.short_description = 'Status'
    
    actions = ['activate_users', 'deactivate_users', 'unlock_accounts', 'verify_emails']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def unlock_accounts(self, request, queryset):
        """Unlock selected accounts"""
        count = 0
        for user in queryset:
            if user.is_locked:
                user.unlock_account()
                count += 1
        self.message_user(request, f'{count} account(s) unlocked successfully.')
    unlock_accounts.short_description = 'Unlock selected accounts'
    
    def verify_emails(self, request, queryset):
        """Verify emails for selected users"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} email(s) verified successfully.')
    verify_emails.short_description = 'Verify emails'


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Admin for RefreshToken model"""
    
    list_display = [
        'user', 'device_name', 'ip_address', 'status_badge',
        'created_at', 'expires_at', 'last_used_at'
    ]
    list_filter = ['is_revoked', 'created_at', 'expires_at']
    search_fields = ['user__email', 'device_name', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'token', 'device_name', 'ip_address', 'user_agent',
        'created_at', 'expires_at', 'last_used_at', 'is_revoked', 'revoked_at'
    ]
    
    def status_badge(self, obj):
        """Display token status with color coding"""
        if obj.is_revoked:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; '
                'border-radius: 3px;">❌ REVOKED</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; '
                'border-radius: 3px;">⏰ EXPIRED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✅ ACTIVE</span>'
            )
    status_badge.short_description = 'Status'
    
    actions = ['revoke_tokens']
    
    def revoke_tokens(self, request, queryset):
        """Revoke selected tokens"""
        count = 0
        for token in queryset.filter(is_revoked=False):
            token.revoke()
            count += 1
        self.message_user(request, f'{count} token(s) revoked successfully.')
    revoke_tokens.short_description = 'Revoke selected tokens'
    
    def has_add_permission(self, request):
        """Disable manual token creation"""
        return False


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for LoginHistory model"""
    
    list_display = [
        'email_attempted', 'user_display', 'status_badge', 'ip_address',
        'country', 'city', 'timestamp'
    ]
    list_filter = ['status', 'timestamp', 'country']
    search_fields = ['email_attempted', 'user__email', 'ip_address']
    ordering = ['-timestamp']
    readonly_fields = [
        'user', 'email_attempted', 'status', 'failure_reason',
        'ip_address', 'user_agent', 'device_info', 'country', 'city', 'timestamp'
    ]
    
    def user_display(self, obj):
        """Display user email or N/A"""
        return obj.user.email if obj.user else 'N/A'
    user_display.short_description = 'User'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        status_colors = {
            'SUCCESS': 'green',
            'FAILED': 'red',
            'LOCKED': 'orange',
            'INACTIVE': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable manual entry creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing"""
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for PasswordResetToken model"""
    
    list_display = [
        'user', 'status_badge', 'created_at', 'expires_at', 'ip_address'
    ]
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'token', 'created_at', 'expires_at',
        'is_used', 'used_at', 'ip_address'
    ]
    
    def status_badge(self, obj):
        """Display token status"""
        if obj.is_used:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✅ USED</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; '
                'border-radius: 3px;">⏰ EXPIRED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">🔓 VALID</span>'
            )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable manual token creation"""
        return False


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for EmailVerificationToken model"""
    
    list_display = [
        'user', 'status_badge', 'created_at', 'expires_at'
    ]
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'token', 'created_at', 'expires_at', 'is_used', 'used_at'
    ]
    
    def status_badge(self, obj):
        """Display token status"""
        if obj.is_used:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 10px; '
                'border-radius: 3px;">✅ USED</span>'
            )
        elif obj.is_expired:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; '
                'border-radius: 3px;">⏰ EXPIRED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; '
                'border-radius: 3px;">📧 VALID</span>'
            )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Disable manual token creation"""
        return False