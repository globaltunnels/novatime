from django.apps import AppConfig


class SeoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.seo'
    verbose_name = 'SEO'

    def ready(self):
        # Import signals or perform app initialization here
        pass