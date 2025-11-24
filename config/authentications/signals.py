"""
Authentication Signals for Mahad Group Accounting Suite
File: apps/auth/signals.py

This module contains signal handlers for authentication events like
user creation, password changes, account locking, and login tracking.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import User, LoginHistory, RefreshToken
from .utils import send_password_changed_notification, send_account_locked_notification


@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler when a new user is created
    """
    if created:
        print(f"✅ New user registered: {instance.email} with role {instance.role}")
        
        # Log user creation
        # You can add additional logic here like:
        # - Creating default user preferences
        # - Setting up user workspace
        # - Notifying admins of new registration
        
        # Example: Create audit log entry
        # AuditLog.objects.create(
        #     action='USER_CREATED',
        #     user=instance,
        #     details=f'New user {instance.email} registered'
        # )


@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, **kwargs):
    """
    Signal handler before user is saved
    Handles password change detection and account locking
    """
    if instance.pk:  # Only for existing users
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # 1. Detect password change
            if old_instance.password != instance.password:
                print(f"🔐 Password changed for user: {instance.email}")
                
                # Update password changed timestamp
                instance.password_changed_at = timezone.now()
                
                # Send notification email (optional - uncomment if needed)
                # Note: You may want to handle this in the view instead
                # to avoid sending duplicate emails
                # try:
                #     send_password_changed_notification(instance)
                # except Exception as e:
                #     print(f"❌ Failed to send password change notification: {e}")
            
            # 2. Detect account locking
            if not old_instance.account_locked_until and instance.account_locked_until:
                print(f"🔒 Account locked: {instance.email} until {instance.account_locked_until}")
                
                # Send lock notification (optional - uncomment if needed)
                # try:
                #     send_account_locked_notification(instance, instance.account_locked_until)
                # except Exception as e:
                #     print(f"❌ Failed to send account lock notification: {e}")
            
            # 3. Detect account unlocking
            if old_instance.account_locked_until and not instance.account_locked_until:
                print(f"🔓 Account unlocked: {instance.email}")
            
            # 4. Detect account deactivation
            if old_instance.is_active and not instance.is_active:
                print(f"⛔ Account deactivated: {instance.email}")
                
                # Revoke all active sessions when account is deactivated
                RefreshToken.objects.filter(
                    user=instance,
                    is_revoked=False
                ).update(
                    is_revoked=True,
                    revoked_at=timezone.now()
                )
                print(f"🔒 All sessions revoked for deactivated user: {instance.email}")
            
            # 5. Detect account reactivation
            if not old_instance.is_active and instance.is_active:
                print(f"✅ Account reactivated: {instance.email}")
            
            # 6. Detect email verification
            if not old_instance.is_verified and instance.is_verified:
                print(f"✉️ Email verified for user: {instance.email}")
                
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=LoginHistory)
def login_history_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler when login history is recorded
    Used for security monitoring and alerts
    """
    if created:
        # 1. Monitor failed login attempts
        if instance.status == 'FAILED':
            # Count recent failed attempts for this email
            recent_failures = LoginHistory.objects.filter(
                email_attempted=instance.email_attempted,
                status='FAILED',
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=15)
            ).count()
            
            if recent_failures >= 3:
                print(f"⚠️ WARNING: {recent_failures} failed login attempts for {instance.email_attempted}")
            
            if recent_failures >= 5:
                print(f"🚨 SECURITY ALERT: Multiple failed login attempts for {instance.email_attempted}")
                # TODO: Send alert to security team/admins
                # send_security_alert(instance.email_attempted, recent_failures)
        
        # 2. Detect logins from new IPs (potential security risk)
        if instance.status == 'SUCCESS' and instance.user:
            previous_ips = LoginHistory.objects.filter(
                user=instance.user,
                status='SUCCESS',
                timestamp__lt=instance.timestamp
            ).values_list('ip_address', flat=True).distinct()
            
            if instance.ip_address and instance.ip_address not in previous_ips and len(previous_ips) > 0:
                print(f"🌍 New IP detected for user {instance.user.email}: {instance.ip_address}")
                # TODO: Send notification about new device/location
                # send_new_login_notification(instance.user, instance.ip_address)
        
        # 3. Monitor account lockouts
        if instance.status == 'LOCKED':
            print(f"🔒 Login attempt blocked (account locked): {instance.email_attempted}")


@receiver(post_delete, sender=RefreshToken)
def refresh_token_deleted_handler(sender, instance, **kwargs):
    """
    Signal handler when refresh token is deleted
    """
    print(f"🗑️ Refresh token deleted for user: {instance.user.email}")


@receiver(post_save, sender=RefreshToken)
def refresh_token_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler when refresh token is created or updated
    """
    if created:
        print(f"🎫 New session created for user: {instance.user.email} from {instance.ip_address}")
        
        # Check if user has too many active sessions
        active_sessions = RefreshToken.objects.filter(
            user=instance.user,
            is_revoked=False,
            expires_at__gt=timezone.now()
        ).count()
        
        # Limit to 10 active sessions per user
        if active_sessions > 10:
            print(f"⚠️ WARNING: User {instance.user.email} has {active_sessions} active sessions")
            
            # Optionally revoke oldest sessions
            old_sessions = RefreshToken.objects.filter(
                user=instance.user,
                is_revoked=False,
                expires_at__gt=timezone.now()
            ).order_by('created_at')[:active_sessions - 10]
            
            for session in old_sessions:
                session.revoke()
            
            print(f"🔒 Revoked {len(old_sessions)} oldest sessions for {instance.user.email}")


# Optional: Signal to clean up expired tokens periodically
@receiver(post_save, sender=RefreshToken)
def cleanup_expired_tokens(sender, instance, created, **kwargs):
    """
    Clean up expired tokens when new token is created
    This helps maintain database performance
    """
    if created:
        # Delete expired tokens older than 30 days
        expired_cutoff = timezone.now() - timezone.timedelta(days=30)
        deleted_count = RefreshToken.objects.filter(
            expires_at__lt=expired_cutoff
        ).delete()[0]
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} expired refresh tokens")


# Custom signal handlers for role changes
@receiver(pre_save, sender=User)
def user_role_changed_handler(sender, instance, **kwargs):
    """
    Signal handler when user role is changed
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            if old_instance.role != instance.role:
                print(f"👤 Role changed for {instance.email}: {old_instance.role} → {instance.role}")
                
                # Log role change for audit
                # AuditLog.objects.create(
                #     action='ROLE_CHANGED',
                #     user=instance,
                #     details=f'Role changed from {old_instance.role} to {instance.role}'
                # )
                
        except User.DoesNotExist:
            pass


# Signal to handle company/branch assignment changes
@receiver(pre_save, sender=User)
def user_assignment_changed_handler(sender, instance, **kwargs):
    """
    Signal handler when user company/branch assignment changes
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Company changed
            if old_instance.company != instance.company:
                old_company = old_instance.company.name if old_instance.company else 'None'
                new_company = instance.company.name if instance.company else 'None'
                print(f"🏢 Company changed for {instance.email}: {old_company} → {new_company}")
            
            # Branch changed
            if old_instance.branch != instance.branch:
                old_branch = old_instance.branch.name if old_instance.branch else 'None'
                new_branch = instance.branch.name if instance.branch else 'None'
                print(f"🏪 Branch changed for {instance.email}: {old_branch} → {new_branch}")
                
        except User.DoesNotExist:
            pass