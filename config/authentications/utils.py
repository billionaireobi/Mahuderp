"""
Authentication Utilities for Mahad Group Accounting Suite
File: apps/auth/utils.py

This module contains utility functions for authentication including
IP detection, user agent parsing, email notifications, and helper functions.
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
import re


# ============================================================
# REQUEST UTILITIES
# ============================================================

def get_client_ip(request):
    """
    Get client IP address from request
    Handles proxy forwarding (X-Forwarded-For header)
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'Unknown'


def get_user_agent(request):
    """
    Get user agent string from request
    
    Args:
        request: Django request object
        
    Returns:
        str: User agent string
    """
    return request.META.get('HTTP_USER_AGENT', 'Unknown')


def parse_user_agent(user_agent):
    """
    Parse user agent string to extract device information
    Simple parser - you can use libraries like 'user-agents' for more detailed parsing
    
    Args:
        user_agent (str): User agent string
        
    Returns:
        dict: Dictionary with browser, os, and device type
        
    Example:
        >>> parse_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0')
        {'browser': 'Chrome', 'os': 'Windows', 'device': 'Desktop'}
    """
    info = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop',
        'browser_version': '',
        'os_version': ''
    }
    
    if not user_agent:
        return info
    
    user_agent_lower = user_agent.lower()
    
    # Browser detection (order matters - check specific browsers first)
    if 'edg' in user_agent_lower or 'edge' in user_agent_lower:
        info['browser'] = 'Edge'
        match = re.search(r'edg[e]?/(\d+)', user_agent_lower)
        if match:
            info['browser_version'] = match.group(1)
    elif 'chrome' in user_agent_lower and 'chromium' not in user_agent_lower:
        info['browser'] = 'Chrome'
        match = re.search(r'chrome/(\d+)', user_agent_lower)
        if match:
            info['browser_version'] = match.group(1)
    elif 'firefox' in user_agent_lower:
        info['browser'] = 'Firefox'
        match = re.search(r'firefox/(\d+)', user_agent_lower)
        if match:
            info['browser_version'] = match.group(1)
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        info['browser'] = 'Safari'
        match = re.search(r'version/(\d+)', user_agent_lower)
        if match:
            info['browser_version'] = match.group(1)
    elif 'opera' in user_agent_lower or 'opr' in user_agent_lower:
        info['browser'] = 'Opera'
        match = re.search(r'opr/(\d+)', user_agent_lower)
        if match:
            info['browser_version'] = match.group(1)
    
    # OS detection
    if 'windows nt 10' in user_agent_lower:
        info['os'] = 'Windows 10/11'
        info['os_version'] = '10/11'
    elif 'windows nt' in user_agent_lower:
        info['os'] = 'Windows'
        match = re.search(r'windows nt ([\d.]+)', user_agent_lower)
        if match:
            info['os_version'] = match.group(1)
    elif 'mac os x' in user_agent_lower or 'macos' in user_agent_lower:
        info['os'] = 'macOS'
        match = re.search(r'mac os x ([\d_]+)', user_agent_lower)
        if match:
            info['os_version'] = match.group(1).replace('_', '.')
    elif 'linux' in user_agent_lower:
        info['os'] = 'Linux'
        if 'ubuntu' in user_agent_lower:
            info['os'] = 'Ubuntu'
    elif 'android' in user_agent_lower:
        info['os'] = 'Android'
        match = re.search(r'android ([\d.]+)', user_agent_lower)
        if match:
            info['os_version'] = match.group(1)
    elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
        if 'ipad' in user_agent_lower:
            info['os'] = 'iPadOS'
        else:
            info['os'] = 'iOS'
        match = re.search(r'os ([\d_]+)', user_agent_lower)
        if match:
            info['os_version'] = match.group(1).replace('_', '.')
    
    # Device type detection
    if 'mobile' in user_agent_lower or ('android' in user_agent_lower and 'mobile' in user_agent_lower):
        info['device'] = 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        info['device'] = 'Tablet'
    elif 'android' in user_agent_lower:
        info['device'] = 'Mobile'
    
    return info


def get_device_name(request):
    """
    Generate a friendly device name from user agent
    
    Args:
        request: Django request object
        
    Returns:
        str: Friendly device name like "Chrome on Windows"
    """
    user_agent = get_user_agent(request)
    device_info = parse_user_agent(user_agent)
    
    browser = device_info['browser']
    os = device_info['os']
    device = device_info['device']
    
    if browser != 'Unknown' and os != 'Unknown':
        return f"{browser} on {os}"
    elif browser != 'Unknown':
        return f"{browser} on {device}"
    elif os != 'Unknown':
        return f"{os} {device}"
    else:
        return device


# ============================================================
# EMAIL UTILITIES
# ============================================================

def send_password_reset_email(user, token):
    """
    Send password reset email to user
    
    Args:
        user: User object
        token: Password reset token
        
    Raises:
        Exception: If email fails to send
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = 'Password Reset Request - Mahad Group Accounting'
    
    context = {
        'user': user,
        'reset_url': reset_url,
        'company_name': 'Mahad Group',
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'expiry_hours': 1,
        'year': datetime.now().year
    }
    
    # Try to render HTML template
    try:
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = strip_tags(html_message)
    except Exception as e:
        print(f"Template not found, using plain text: {e}")
        # Fallback to plain text if template doesn't exist
        plain_message = f"""
Hello {user.first_name},

You requested a password reset for your Mahad Group Accounting account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

For security reasons, we cannot show you your current password.

Best regards,
Mahad Group Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
        """
        html_message = None
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Password reset email sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        raise


def send_verification_email(user, token):
    """
    Send email verification to user
    
    Args:
        user: User object
        token: Email verification token
        
    Raises:
        Exception: If email fails to send
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    subject = 'Verify Your Email - Mahad Group Accounting'
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'company_name': 'Mahad Group',
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'year': datetime.now().year
    }
    
    # Try to render HTML template
    try:
        html_message = render_to_string('emails/email_verification.html', context)
        plain_message = strip_tags(html_message)
    except Exception as e:
        print(f"Template not found, using plain text: {e}")
        # Fallback to plain text if template doesn't exist
        plain_message = f"""
Hello {user.first_name},

Welcome to Mahad Group Accounting Suite!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

Once verified, you'll have full access to your account.

Best regards,
Mahad Group Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
        """
        html_message = None
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Verification email sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        raise


def send_password_changed_notification(user):
    """
    Send notification when password is changed
    
    Args:
        user: User object
        
    Raises:
        Exception: If email fails to send
    """
    subject = 'Password Changed - Mahad Group Accounting'
    
    context = {
        'user': user,
        'company_name': 'Mahad Group',
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'year': datetime.now().year,
        'frontend_url': settings.FRONTEND_URL
    }
    
    # Try to render HTML template
    try:
        html_message = render_to_string('emails/password_changed.html', context)
        plain_message = strip_tags(html_message)
    except Exception as e:
        print(f"Template not found, using plain text: {e}")
        # Fallback to plain text if template doesn't exist
        plain_message = f"""
Hello {user.first_name},

Your password for Mahad Group Accounting was recently changed.

If you made this change, you can safely ignore this email.

If you did NOT make this change, please:
1. Reset your password immediately at {settings.FRONTEND_URL}/reset-password
2. Contact support at {settings.DEFAULT_FROM_EMAIL}

This is a security notification to help protect your account.

Best regards,
Mahad Group Security Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
        """
        html_message = None
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Password change notification sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send password change notification: {e}")
        raise


def send_account_locked_notification(user, unlock_time):
    """
    Send notification when account is locked
    
    Args:
        user: User object
        unlock_time: DateTime when account will be unlocked
        
    Raises:
        Exception: If email fails to send
    """
    from django.utils import timezone
    
    subject = 'Account Locked - Mahad Group Accounting'
    
    minutes_locked = int((unlock_time - timezone.now()).total_seconds() / 60)
    
    plain_message = f"""
Hello {user.first_name},

Your Mahad Group Accounting account has been temporarily locked due to multiple failed login attempts.

Security Details:
- Your account will be automatically unlocked in {minutes_locked} minutes
- Locked until: {unlock_time.strftime('%Y-%m-%d %H:%M:%S')}
- Multiple failed login attempts were detected

If you didn't attempt to login, please contact support immediately at {settings.DEFAULT_FROM_EMAIL}.

For your security:
- This is an automatic security measure
- Your account will unlock automatically
- All login attempts are logged

Best regards,
Mahad Group Security Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"✅ Account lock notification sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send account lock notification: {e}")


def send_new_login_notification(user, ip_address, device_info):
    """
    Send notification for new login from unrecognized device
    
    Args:
        user: User object
        ip_address: IP address of login
        device_info: Dictionary with device information
        
    Raises:
        Exception: If email fails to send
    """
    from django.utils import timezone
    
    subject = 'New Login Detected - Mahad Group Accounting'
    
    login_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    
    plain_message = f"""
Hello {user.first_name},

A new login to your Mahad Group Accounting account was detected.

Login Details:
- Time: {login_time}
- IP Address: {ip_address}
- Device: {device_info.get('device', 'Unknown')}
- Browser: {device_info.get('browser', 'Unknown')} {device_info.get('browser_version', '')}
- Operating System: {device_info.get('os', 'Unknown')} {device_info.get('os_version', '')}

If this was you, you can safely ignore this email.

If you don't recognize this login, please secure your account immediately:
1. Change your password at {settings.FRONTEND_URL}/change-password
2. Review active sessions in your account settings
3. Revoke any suspicious sessions
4. Contact support at {settings.DEFAULT_FROM_EMAIL}

Best regards,
Mahad Group Security Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"✅ New login notification sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send new login notification: {e}")


def send_welcome_email(user):
    """
    Send welcome email to new user
    
    Args:
        user: User object
        
    Raises:
        Exception: If email fails to send
    """
    subject = 'Welcome to Mahad Group Accounting Suite'
    
    plain_message = f"""
Hello {user.first_name},

Welcome to Mahad Group Accounting Suite!

Your account has been successfully created with the following details:
- Email: {user.email}
- Role: {user.get_role_display()}
- Company: {user.company.name if user.company else 'Not assigned'}

You can now access the system at {settings.FRONTEND_URL}

Getting Started:
1. Verify your email address
2. Complete your profile
3. Explore the features based on your role

If you have any questions, please contact support at {settings.DEFAULT_FROM_EMAIL}.

Best regards,
Mahad Group Team

---
This is an automated message, please do not reply to this email.
Support: {settings.DEFAULT_FROM_EMAIL}
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"✅ Welcome email sent to {user.email}")
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")


# ============================================================
# VALIDATION UTILITIES
# ============================================================

def validate_email_format(email):
    """
    Validate email format using regex
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_format(phone):
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces and special characters
    cleaned = re.sub(r'[^\d+]', '', phone)
    # Must start with + and have at least 10 digits
    return bool(re.match(r'^\+?\d{10,15}$', cleaned))


def sanitize_filename(filename):
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove path separators and special characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    name = name[:50]  # Limit name to 50 chars
    return f"{name}.{ext}" if ext else name


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_username_from_email(email):
    """
    Generate username from email address
    
    Args:
        email (str): Email address
        
    Returns:
        str: Generated username
    """
    return email.split('@')[0].lower()


def mask_email(email):
    """
    Mask email for privacy (show first 2 and last 2 chars of local part)
    
    Args:
        email (str): Email address
        
    Returns:
        str: Masked email
        
    Example:
        >>> mask_email('john.doe@example.com')
        'jo****oe@example.com'
    """
    if '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 4:
        return f"{local[0]}***@{domain}"
    
    return f"{local[:2]}{'*' * (len(local) - 4)}{local[-2:]}@{domain}"


def format_time_ago(timestamp):
    """
    Format timestamp as 'time ago' string
    
    Args:
        timestamp: DateTime object
        
    Returns:
        str: Formatted time string
        
    Example:
        '2 minutes ago', '1 hour ago', '3 days ago'
    """
    from django.utils import timezone
    
    now = timezone.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'