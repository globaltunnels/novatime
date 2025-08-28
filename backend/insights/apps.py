from django.apps import AppConfig


class InsightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.insights'
    verbose_name = 'Insights'

    def ready(self):
        # Import signals or perform app initialization here
        pass