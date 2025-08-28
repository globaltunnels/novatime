from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.accounts_app'
    verbose_name = 'Accounts'

    def ready(self):
        # Import signals or perform app initialization here
        pass