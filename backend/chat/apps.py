from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    verbose_name = 'Real-time Chat'
    
    def ready(self):
        """App ready signal handler."""
        import chat.signals  # Import signal handlers