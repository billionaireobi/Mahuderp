from django.apps import AppConfig


class AuthenticationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentications'
    verbose_name = 'Authentications'
    def ready(self):
        """
        Import signal handlers when the app is ready
        """
        
        def ready(self):
            import authentications.signals  # noqa
