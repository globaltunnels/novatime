from django.apps import AppConfig


class IamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.iam'
    verbose_name = 'IAM'

    def ready(self):
        # Import signals or perform app initialization here
        pass