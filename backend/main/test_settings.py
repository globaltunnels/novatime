"""
Django settings for testing purposes.
"""

from .settings import *

# Use an in-memory SQLite database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use a faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging for tests
LOGGING_CONFIG = None

# Disable rate limiting for tests
RATELIMIT_ENABLE = False

# OAuth2 provider settings for tests
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'
# Remove PostgreSQL-specific apps that cause issues in testing
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.postgres']

# Disable problematic middleware for tests
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'prometheus' not in mw.lower()]

# Disable channels for tests (Redis dependency)
CHANNEL_LAYERS = {}

# Disable Celery for tests
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
OAUTH2_PROVIDER_ID_TOKEN_MODEL = 'oauth2_provider.IDToken'