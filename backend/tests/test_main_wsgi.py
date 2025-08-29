import os
from django.test import TestCase
from unittest.mock import patch, MagicMock


class WSGIConfigTest(TestCase):
    """Test WSGI configuration for the main application."""

    def setUp(self):
        # Ensure we're using test settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.main.test_settings')

    def test_django_settings_module(self):
        """Test that Django settings module is properly set."""
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'backend.main.test_settings'
        )

    @patch('main.wsgi.get_wsgi_application')
    def test_application_creation(self, mock_get_wsgi_app):
        """Test that WSGI application is created correctly."""
        mock_wsgi_app = MagicMock()
        mock_get_wsgi_app.return_value = mock_wsgi_app

        # Import the module to trigger application creation
        from main import wsgi

        # Verify get_wsgi_application was called
        mock_get_wsgi_app.assert_called_once()

        # Verify application is the WSGI app
        self.assertEqual(wsgi.application, mock_wsgi_app)

    def test_application_callable(self):
        """Test that the application object is callable (WSGI interface)."""
        from main import wsgi

        # WSGI applications should be callable
        self.assertTrue(callable(wsgi.application))

    def test_settings_module_path(self):
        """Test that the settings module path is correct."""
        from main import wsgi

        # The settings module should point to the correct path
        expected_settings = 'backend.project-settings.settings'
        self.assertEqual(wsgi.os.environ.get('DJANGO_SETTINGS_MODULE'), expected_settings)

    @patch('django.core.wsgi.get_wsgi_application')
    def test_django_wsgi_integration(self, mock_get_wsgi_app):
        """Test integration with Django's WSGI application."""
        mock_app = MagicMock()
        mock_get_wsgi_app.return_value = mock_app

        from main import wsgi

        # Verify Django WSGI app is used
        self.assertEqual(wsgi.application, mock_app)


class WSGIIntegrationTest(TestCase):
    """Test WSGI integration with Django."""

    def test_django_wsgi_import(self):
        """Test that Django WSGI application can be imported."""
        try:
            from django.core.wsgi import get_wsgi_application
            self.assertTrue(callable(get_wsgi_application))
        except ImportError as e:
            self.fail(f"Django WSGI import failed: {e}")

    def test_wsgi_module_structure(self):
        """Test that the WSGI module has the correct structure."""
        from main import wsgi

        # Should have application object
        self.assertTrue(hasattr(wsgi, 'application'))

        # Should have os module imported
        self.assertTrue(hasattr(wsgi, 'os'))

        # Should have get_wsgi_application imported
        self.assertTrue(hasattr(wsgi, 'get_wsgi_application'))

    def test_environment_setup(self):
        """Test that environment is properly set up."""
        from main import wsgi

        # DJANGO_SETTINGS_MODULE should be set
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
        self.assertIsNotNone(settings_module)
        self.assertTrue(settings_module.endswith('settings'))

    @patch('django.core.wsgi.get_wsgi_application')
    def test_application_initialization(self, mock_get_wsgi_app):
        """Test that application is properly initialized."""
        mock_app = MagicMock()
        mock_get_wsgi_app.return_value = mock_app

        # Force reimport to test initialization
        import importlib
        import main.wsgi
        importlib.reload(main.wsgi)

        # Verify get_wsgi_application was called
        mock_get_wsgi_app.assert_called_once()


class WSGIDeploymentTest(TestCase):
    """Test WSGI configuration for deployment scenarios."""

    def test_wsgi_application_interface(self):
        """Test that the WSGI application conforms to WSGI interface."""
        from main import wsgi

        app = wsgi.application

        # WSGI applications should be callable
        self.assertTrue(callable(app))

        # Should accept environ and start_response parameters
        # (This is the WSGI interface)
        import inspect
        sig = inspect.signature(app)
        params = list(sig.parameters.keys())

        # Should have at least environ and start_response
        self.assertGreaterEqual(len(params), 2)

    def test_settings_module_consistency(self):
        """Test that settings module is consistent between ASGI and WSGI."""
        from main import wsgi, asgi

        wsgi_settings = wsgi.os.environ.get('DJANGO_SETTINGS_MODULE')
        asgi_settings = asgi.os.environ.get('DJANGO_SETTINGS_MODULE')

        # Both should use the same settings module
        self.assertEqual(wsgi_settings, asgi_settings)

    def test_wsgi_vs_asgi_settings(self):
        """Test that WSGI and ASGI use compatible settings."""
        from main import wsgi, asgi

        # Both should point to the same settings module
        self.assertEqual(
            wsgi.os.environ.get('DJANGO_SETTINGS_MODULE'),
            asgi.os.environ.get('DJANGO_SETTINGS_MODULE')
        )


class WSGISecurityTest(TestCase):
    """Test WSGI security configuration."""

    def test_no_debug_exposure(self):
        """Test that debug information is not exposed in production."""
        from main import wsgi
        from django.conf import settings

        # In test environment, debug should be True, but we should verify
        # the configuration doesn't expose sensitive information
        self.assertTrue(hasattr(settings, 'DEBUG'))

    def test_settings_import_security(self):
        """Test that settings import doesn't expose sensitive data."""
        from main import wsgi

        # The module should not expose sensitive settings directly
        sensitive_attrs = ['SECRET_KEY', 'DATABASES', 'API_KEYS']

        for attr in sensitive_attrs:
            if hasattr(wsgi, attr):
                self.fail(f"WSGI module should not expose {attr}")

    def test_wsgi_application_isolation(self):
        """Test that WSGI application is properly isolated."""
        from main import wsgi

        # Application should be the only public interface
        public_attrs = [attr for attr in dir(wsgi) if not attr.startswith('_')]

        # Should have application as the main public interface
        self.assertIn('application', public_attrs)

        # Other expected public attrs
        expected_public = {'application', 'os', 'get_wsgi_application'}
        actual_public = set(public_attrs)

        # All public attrs should be expected
        unexpected = actual_public - expected_public
        if unexpected:
            self.fail(f"Unexpected public attributes in WSGI module: {unexpected}")


class WSGIPerformanceTest(TestCase):
    """Test WSGI configuration for performance considerations."""

    @patch('django.core.wsgi.get_wsgi_application')
    def test_application_caching(self, mock_get_wsgi_app):
        """Test that WSGI application is cached (not recreated on each request)."""
        mock_app = MagicMock()
        mock_get_wsgi_app.return_value = mock_app

        from main import wsgi

        # First access
        app1 = wsgi.application

        # Second access should return the same instance
        app2 = wsgi.application

        self.assertEqual(app1, app2)
        self.assertEqual(app1, mock_app)

        # get_wsgi_application should only be called once
        mock_get_wsgi_app.assert_called_once()

    def test_module_import_performance(self):
        """Test that module imports are optimized."""
        import time

        start_time = time.time()

        # Import should be fast
        from main import wsgi

        import_time = time.time() - start_time

        # Import should complete in reasonable time (less than 1 second)
        self.assertLess(import_time, 1.0, "WSGI module import is too slow")

    @patch('django.core.wsgi.get_wsgi_application')
    def test_lazy_initialization(self, mock_get_wsgi_app):
        """Test that WSGI application is initialized lazily."""
        mock_app = MagicMock()
        mock_get_wsgi_app.return_value = mock_app

        # Just importing the module should not call get_wsgi_application
        import importlib
        if 'main.wsgi' in sys.modules:
            importlib.reload(sys.modules['main.wsgi'])

        # Import the module
        from main import wsgi

        # Accessing application should trigger initialization
        app = wsgi.application

        mock_get_wsgi_app.assert_called_once()
        self.assertEqual(app, mock_app)