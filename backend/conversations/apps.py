from django.apps import AppConfig


class ConversationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.conversations'
    verbose_name = 'Conversations'

    def ready(self):
        # Import signals or perform app initialization here
        pass