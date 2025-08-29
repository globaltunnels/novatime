import os
import sys
from django.test import TestCase
from unittest.mock import patch, MagicMock
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack


class ASGIConfigTest(TestCase):
    """Test ASGI configuration for the main application."""

    def setUp(self):
        # Ensure we're using test settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.main.test_settings')

    def test_django_settings_module(self):
        """Test that Django settings module is properly set."""
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'backend.main.test_settings'
        )

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns', [])
    def test_application_creation(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that ASGI application is created correctly."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        # Import the module to trigger application creation
        from main import asgi

        # Verify Django ASGI app was initialized
        mock_get_asgi_app.assert_called_once()

        # Verify application is a ProtocolTypeRouter
        self.assertIsInstance(asgi.application, ProtocolTypeRouter)

        # Verify application has both http and websocket protocols
        protocols = asgi.application.application_mapping
        self.assertIn('http', protocols)
        self.assertIn('websocket', protocols)

        # Verify HTTP protocol uses Django ASGI app
        self.assertEqual(protocols['http'], mock_django_app)

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns')
    def test_websocket_protocol_configuration(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that WebSocket protocol is properly configured."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        # Mock websocket URL patterns
        mock_websocket_patterns.__iter__ = lambda self: iter([])

        # Import the module to trigger application creation
        from main import asgi

        websocket_app = asgi.application.application_mapping['websocket']

        # Verify WebSocket app is wrapped with security middleware
        self.assertIsInstance(websocket_app, AllowedHostsOriginValidator)

        # Verify auth middleware is applied
        auth_middleware = websocket_app.application
        self.assertIsInstance(auth_middleware, AuthMiddlewareStack)

        # Verify URLRouter is used
        url_router = auth_middleware.application
        self.assertIsInstance(url_router, URLRouter)

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns', [])
    def test_websocket_urlpatterns_import(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that websocket URL patterns are properly imported."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        # Import the module
        from main import asgi

        # Verify websocket_urlpatterns was imported from websocket_server.routing
        from websocket_server.routing import websocket_urlpatterns as expected_patterns
        self.assertEqual(asgi.websocket_urlpatterns, expected_patterns)

    def test_application_callable(self):
        """Test that the application object is callable (ASGI interface)."""
        from main import asgi

        # ASGI applications should be callable
        self.assertTrue(callable(asgi.application))

    def test_application_has_required_attributes(self):
        """Test that the application has required ASGI attributes."""
        from main import asgi

        # Check that application has the expected structure
        self.assertTrue(hasattr(asgi.application, 'application_mapping'))

        mapping = asgi.application.application_mapping
        self.assertIsInstance(mapping, dict)
        self.assertIn('http', mapping)
        self.assertIn('websocket', mapping)

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns', [])
    def test_django_app_initialization_order(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that Django ASGI app is initialized before importing models."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        # Import should trigger Django app initialization
        from main import asgi

        # Verify get_asgi_application was called early
        mock_get_asgi_app.assert_called_once()

        # Verify django_asgi_app is set
        self.assertEqual(asgi.django_asgi_app, mock_django_app)

    def test_settings_module_path(self):
        """Test that the settings module path is correct."""
        from main import asgi

        # The settings module should point to the correct path
        expected_settings = 'backend.project-settings.settings'
        self.assertEqual(asgi.os.environ.get('DJANGO_SETTINGS_MODULE'), expected_settings)


class ASGIIntegrationTest(TestCase):
    """Test ASGI integration with Django and Channels."""

    def test_channels_imports(self):
        """Test that all required Channels imports are available."""
        try:
            from channels.auth import AuthMiddlewareStack
            from channels.routing import ProtocolTypeRouter, URLRouter
            from channels.security.websocket import AllowedHostsOriginValidator
            from django.core.asgi import get_asgi_application
        except ImportError as e:
            self.fail(f"Required Channels import failed: {e}")

    def test_websocket_routing_import(self):
        """Test that websocket routing can be imported."""
        try:
            from websocket_server.routing import websocket_urlpatterns
            self.assertIsInstance(websocket_urlpatterns, list)
        except ImportError as e:
            self.fail(f"WebSocket routing import failed: {e}")

    @patch('django.core.asgi.get_asgi_application')
    def test_django_asgi_integration(self, mock_get_asgi_app):
        """Test integration with Django's ASGI application."""
        mock_app = MagicMock()
        mock_get_asgi_app.return_value = mock_app

        from main import asgi

        # Verify Django ASGI app is used in the protocol router
        http_app = asgi.application.application_mapping['http']
        self.assertEqual(http_app, mock_app)

    def test_protocol_router_structure(self):
        """Test that the ProtocolTypeRouter has the correct structure."""
        from main import asgi

        router = asgi.application

        # Should have both http and websocket protocols
        self.assertIn('http', router.application_mapping)
        self.assertIn('websocket', router.application_mapping)

        # Each protocol should have an application
        for protocol, app in router.application_mapping.items():
            self.assertIsNotNone(app, f"Protocol {protocol} has no application")


class ASGISecurityTest(TestCase):
    """Test ASGI security configuration."""

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns', [])
    def test_allowed_hosts_validator(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that WebSocket connections use AllowedHostsOriginValidator."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        from main import asgi

        websocket_app = asgi.application.application_mapping['websocket']

        # Should be wrapped with AllowedHostsOriginValidator
        self.assertIsInstance(websocket_app, AllowedHostsOriginValidator)

    @patch('main.asgi.get_asgi_application')
    @patch('main.asgi.websocket_urlpatterns', [])
    def test_auth_middleware_stack(self, mock_websocket_patterns, mock_get_asgi_app):
        """Test that WebSocket connections use AuthMiddlewareStack."""
        mock_django_app = MagicMock()
        mock_get_asgi_app.return_value = mock_django_app

        from main import asgi

        websocket_app = asgi.application.application_mapping['websocket']
        auth_app = websocket_app.application

        # Should be wrapped with AuthMiddlewareStack
        self.assertIsInstance(auth_app, AuthMiddlewareStack)

    def test_websocket_url_patterns_security(self):
        """Test that WebSocket URL patterns are properly secured."""
        from websocket_server.routing import websocket_urlpatterns

        # All WebSocket patterns should exist and be properly configured
        self.assertGreater(len(websocket_urlpatterns), 0)

        for pattern in websocket_urlpatterns:
            # Each pattern should have a callback (consumer)
            self.assertTrue(hasattr(pattern, 'callback'))
            # Callback should be an ASGI application (have as_asgi method)
            self.assertTrue(hasattr(pattern.callback, 'as_asgi'))