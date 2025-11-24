# ============================================================
# File: core/__init__.py
# ============================================================
"""
Core app for Mahad Group Accounting Suite
Contains core business models
"""

default_app_config = 'core.apps.CoreConfig'


# ============================================================
# File: core/apps.py
# ============================================================
"""
Core App Configuration
File: core/apps.py
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Models'
    
    def ready(self):
        """
        Import signal handlers when the app is ready
        """
        # Import signals here if needed
        pass