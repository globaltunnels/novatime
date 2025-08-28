from django.apps import AppConfig


class AbtestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.abtests'
    verbose_name = 'A/B Tests'

    def ready(self):
        # Import signals or perform app initialization here
        pass