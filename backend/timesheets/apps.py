from django.apps import AppConfig


class TimesheetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.timesheets'
    verbose_name = 'Timesheets'

    def ready(self):
        # Import signals or perform app initialization here
        pass