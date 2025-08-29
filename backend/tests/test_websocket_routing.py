from django.test import TestCase
from django.urls import re_path
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from websocket_server.routing import websocket_urlpatterns
from websocket_server.consumers import LiveUpdatesConsumer, ChatConsumer
import uuid


class WebSocketRoutingTest(TestCase):
    """Test WebSocket URL routing configuration."""

    def test_websocket_urlpatterns_structure(self):
        """Test that websocket_urlpatterns has correct structure."""
        self.assertIsInstance(websocket_urlpatterns, list)
        self.assertEqual(len(websocket_urlpatterns), 2)

        # Check first pattern (live updates)
        live_updates_pattern = websocket_urlpatterns[0]
        self.assertIsInstance(live_updates_pattern, re_path)

        # Check second pattern (chat)
        chat_pattern = websocket_urlpatterns[1]
        self.assertIsInstance(chat_pattern, re_path)

    def test_live_updates_url_pattern(self):
        """Test live updates WebSocket URL pattern."""
        pattern = websocket_urlpatterns[0]

        # Check pattern regex
        expected_pattern = r'ws/live-updates/(?P<workspace_id>[0-9a-f-]+)/$'
        self.assertEqual(pattern.pattern.regex.pattern, expected_pattern)

        # Check consumer
        self.assertEqual(pattern.callback, LiveUpdatesConsumer.as_asgi())

    def test_chat_url_pattern(self):
        """Test chat WebSocket URL pattern."""
        pattern = websocket_urlpatterns[1]

        # Check pattern regex
        expected_pattern = r'ws/chat/(?P<workspace_id>[0-9a-f-]+)/(?P<room_type>\w+)/(?P<room_id>[0-9a-f-]+)/$'
        self.assertEqual(pattern.pattern.regex.pattern, expected_pattern)

        # Check consumer
        self.assertEqual(pattern.callback, ChatConsumer.as_asgi())

    def test_live_updates_url_matching(self):
        """Test live updates URL matching."""
        pattern = websocket_urlpatterns[0]

        # Valid workspace ID
        workspace_id = str(uuid.uuid4())
        path = f'/ws/live-updates/{workspace_id}/'

        match = pattern.pattern.match(path)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict()['workspace_id'], workspace_id)

    def test_chat_url_matching(self):
        """Test chat URL matching."""
        pattern = websocket_urlpatterns[1]

        # Valid chat URL
        workspace_id = str(uuid.uuid4())
        room_type = 'workspace'
        room_id = str(uuid.uuid4())
        path = f'/ws/chat/{workspace_id}/{room_type}/{room_id}/'

        match = pattern.pattern.match(path)
        self.assertIsNotNone(match)

        groups = match.groupdict()
        self.assertEqual(groups['workspace_id'], workspace_id)
        self.assertEqual(groups['room_type'], room_type)
        self.assertEqual(groups['room_id'], room_id)

    def test_invalid_live_updates_urls(self):
        """Test invalid live updates URLs don't match."""
        pattern = websocket_urlpatterns[0]

        invalid_paths = [
            '/ws/live-updates/',  # Missing workspace ID
            '/ws/live-updates/invalid-id/',  # Invalid UUID format
            '/ws/live-updates/123/extra/',  # Extra path components
            '/ws/live-updates/123',  # Missing trailing slash
        ]

        for path in invalid_paths:
            match = pattern.pattern.match(path)
            self.assertIsNone(match, f"Path {path} should not match")

    def test_invalid_chat_urls(self):
        """Test invalid chat URLs don't match."""
        pattern = websocket_urlpatterns[1]

        invalid_paths = [
            '/ws/chat/',  # Missing all parameters
            '/ws/chat/workspace_id/',  # Missing room_type and room_id
            '/ws/chat/workspace_id/room_type/',  # Missing room_id
            '/ws/chat/workspace_id/room_type/room_id/extra/',  # Extra components
            '/ws/chat/workspace_id/room_type/room_id',  # Missing trailing slash
        ]

        for path in invalid_paths:
            match = pattern.pattern.match(path)
            self.assertIsNone(match, f"Path {path} should not match")

    def test_url_pattern_names(self):
        """Test that URL patterns don't have conflicting names."""
        pattern_names = []

        for pattern in websocket_urlpatterns:
            if hasattr(pattern, 'name') and pattern.name:
                pattern_names.append(pattern.name)

        # Should have no duplicate names
        self.assertEqual(len(pattern_names), len(set(pattern_names)))

    def test_urlrouter_integration(self):
        """Test that URLRouter can be created with websocket_urlpatterns."""
        try:
            router = URLRouter(websocket_urlpatterns)
            self.assertIsNotNone(router)
        except Exception as e:
            self.fail(f"URLRouter creation failed: {e}")


class WebSocketURLResolutionTest(TestCase):
    """Test WebSocket URL resolution and routing."""

    def setUp(self):
        self.router = URLRouter(websocket_urlpatterns)

    def test_live_updates_route_resolution(self):
        """Test live updates route resolution."""
        workspace_id = str(uuid.uuid4())
        path = f'/ws/live-updates/{workspace_id}/'

        # The router should be able to handle this path
        # We can't easily test the full resolution without a mock scope,
        # but we can verify the pattern matches
        pattern = websocket_urlpatterns[0]
        match = pattern.pattern.match(path)
        self.assertIsNotNone(match)

        # Verify the matched parameters
        kwargs = match.groupdict()
        self.assertIn('workspace_id', kwargs)
        self.assertEqual(kwargs['workspace_id'], workspace_id)

    def test_chat_route_resolution(self):
        """Test chat route resolution."""
        workspace_id = str(uuid.uuid4())
        room_type = 'project'
        room_id = str(uuid.uuid4())
        path = f'/ws/chat/{workspace_id}/{room_type}/{room_id}/'

        # Verify pattern matches
        pattern = websocket_urlpatterns[1]
        match = pattern.pattern.match(path)
        self.assertIsNotNone(match)

        # Verify the matched parameters
        kwargs = match.groupdict()
        self.assertEqual(kwargs['workspace_id'], workspace_id)
        self.assertEqual(kwargs['room_type'], room_type)
        self.assertEqual(kwargs['room_id'], room_id)

    def test_route_parameter_types(self):
        """Test that route parameters have correct types."""
        # Test workspace_id accepts UUID format
        workspace_id = '12345678-1234-5678-9012-123456789012'
        path1 = f'/ws/live-updates/{workspace_id}/'
        pattern1 = websocket_urlpatterns[0]
        self.assertIsNotNone(pattern1.pattern.match(path1))

        # Test room_type accepts word characters
        room_types = ['workspace', 'project', 'direct', 'channel']
        workspace_id = str(uuid.uuid4())
        room_id = str(uuid.uuid4())

        for room_type in room_types:
            path = f'/ws/chat/{workspace_id}/{room_type}/{room_id}/'
            pattern = websocket_urlpatterns[1]
            match = pattern.pattern.match(path)
            self.assertIsNotNone(match, f"Room type '{room_type}' should match")

    def test_route_precedence(self):
        """Test that more specific routes take precedence."""
        # Both patterns could potentially match similar paths,
        # but they have different structures so there should be no conflict

        workspace_id = str(uuid.uuid4())

        # Live updates path
        live_path = f'/ws/live-updates/{workspace_id}/'
        live_pattern = websocket_urlpatterns[0]
        chat_pattern = websocket_urlpatterns[1]

        # Only live pattern should match live path
        self.assertIsNotNone(live_pattern.pattern.match(live_path))
        self.assertIsNone(chat_pattern.pattern.match(live_path))

        # Chat path
        chat_path = f'/ws/chat/{workspace_id}/workspace/{workspace_id}/'

        # Only chat pattern should match chat path
        self.assertIsNone(live_pattern.pattern.match(chat_path))
        self.assertIsNotNone(chat_pattern.pattern.match(chat_path))


class WebSocketConsumerIntegrationTest(TestCase):
    """Test WebSocket consumer integration with routing."""

    def test_live_updates_consumer_as_asgi(self):
        """Test that LiveUpdatesConsumer can be used as ASGI app."""
        consumer = LiveUpdatesConsumer.as_asgi()
        self.assertIsNotNone(consumer)

        # Should be callable (ASGI interface)
        self.assertTrue(callable(consumer))

    def test_chat_consumer_as_asgi(self):
        """Test that ChatConsumer can be used as ASGI app."""
        consumer = ChatConsumer.as_asgi()
        self.assertIsNotNone(consumer)

        # Should be callable (ASGI interface)
        self.assertTrue(callable(consumer))

    def test_consumer_classes_exist(self):
        """Test that consumer classes exist and are importable."""
        from websocket_server.consumers import LiveUpdatesConsumer, ChatConsumer

        # Should be classes
        self.assertTrue(isinstance(LiveUpdatesConsumer, type))
        self.assertTrue(isinstance(ChatConsumer, type))

        # Should have required methods
        required_methods = ['connect', 'disconnect', 'receive']

        for method in required_methods:
            self.assertTrue(hasattr(LiveUpdatesConsumer, method))
            self.assertTrue(hasattr(ChatConsumer, method))
            self.assertTrue(callable(getattr(LiveUpdatesConsumer, method)))
            self.assertTrue(callable(getattr(ChatConsumer, method)))