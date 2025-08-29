import pytest
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from unittest.mock import patch, MagicMock, AsyncMock
from websocket_server.consumers import LiveUpdatesConsumer, ChatConsumer
from websocket_server.routing import websocket_urlpatterns
from organizations.models import Organization, Workspace, Membership
from projects.models import Project, ProjectMember
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class LiveUpdatesConsumerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create workspace membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        # Create access token
        self.access_token = str(AccessToken.for_user(self.user))

    @patch('websocket_server.consumers.LiveUpdatesConsumer.get_user_from_token')
    @patch('websocket_server.consumers.LiveUpdatesConsumer.verify_workspace_access')
    async def test_successful_connection(self, mock_verify_access, mock_get_user):
        """Test successful WebSocket connection."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_connection_without_token(self):
        """Test connection fails without token."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/'
        )

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_connection_with_invalid_workspace(self):
        """Test connection fails with invalid workspace."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/invalid-workspace-id/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    @patch('websocket_server.consumers.LiveUpdatesConsumer.get_user_from_token')
    async def test_connection_with_unauthenticated_user(self, mock_get_user):
        """Test connection fails with unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser
        mock_get_user.return_value = AnonymousUser()

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    @patch('websocket_server.consumers.LiveUpdatesConsumer.get_user_from_token')
    @patch('websocket_server.consumers.LiveUpdatesConsumer.verify_workspace_access')
    async def test_ping_pong(self, mock_verify_access, mock_get_user):
        """Test ping-pong functionality."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send ping
        await communicator.send_json_to({
            'type': 'ping',
            'timestamp': '2023-01-01T12:00:00Z'
        })

        # Receive pong
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'pong')
        self.assertEqual(response['timestamp'], '2023-01-01T12:00:00Z')

        await communicator.disconnect()

    @patch('websocket_server.consumers.LiveUpdatesConsumer.get_user_from_token')
    @patch('websocket_server.consumers.LiveUpdatesConsumer.verify_workspace_access')
    async def test_workspace_update_broadcast(self, mock_verify_access, mock_get_user):
        """Test workspace update broadcasting."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate workspace update
        await communicator.send_json_to({
            'type': 'workspace_update',
            'event_type': 'test_update',
            'data': {'message': 'test'}
        })

        # Should receive the message back
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'workspace_update')

        await communicator.disconnect()

    @patch('websocket_server.consumers.LiveUpdatesConsumer.get_user_from_token')
    @patch('websocket_server.consumers.LiveUpdatesConsumer.verify_workspace_access')
    @patch('websocket_server.consumers.LiveUpdatesConsumer.verify_project_access')
    async def test_subscription_to_project_channel(self, mock_verify_project, mock_verify_access, mock_get_user):
        """Test subscription to project-specific channel."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True
        mock_verify_project.return_value = True

        # Create a project
        project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project'
        )

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/live-updates/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Subscribe to project channel
        await communicator.send_json_to({
            'type': 'subscribe',
            'channels': [f'project_{project.id}']
        })

        # Should not receive error response (subscription should succeed)
        await communicator.disconnect()


class ChatConsumerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create workspace membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        # Create access token
        self.access_token = str(AccessToken.for_user(self.user))

    @patch('websocket_server.consumers.ChatConsumer.get_user_from_token')
    @patch('websocket_server.consumers.ChatConsumer.verify_room_access')
    async def test_successful_chat_connection(self, mock_verify_access, mock_get_user):
        """Test successful chat WebSocket connection."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_chat_connection_missing_parameters(self):
        """Test chat connection fails with missing parameters."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    @patch('websocket_server.consumers.ChatConsumer.get_user_from_token')
    @patch('websocket_server.consumers.ChatConsumer.verify_room_access')
    @patch('websocket_server.consumers.ChatConsumer.save_chat_message')
    async def test_chat_message_handling(self, mock_save_message, mock_verify_access, mock_get_user):
        """Test chat message handling."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        # Mock saved message
        mock_message = MagicMock()
        mock_message.id = 1
        mock_message.content = 'Test message'
        mock_message.user = self.user
        mock_message.created_at.isoformat.return_value = '2023-01-01T12:00:00Z'
        mock_save_message.return_value = mock_message

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send chat message
        await communicator.send_json_to({
            'type': 'chat_message',
            'message': 'Test message'
        })

        # Should receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['message']['content'], 'Test message')

        await communicator.disconnect()

    @patch('websocket_server.consumers.ChatConsumer.get_user_from_token')
    @patch('websocket_server.consumers.ChatConsumer.verify_room_access')
    async def test_typing_indicators(self, mock_verify_access, mock_get_user):
        """Test typing indicator handling."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send typing start
        await communicator.send_json_to({
            'type': 'typing_start'
        })

        # Send typing stop
        await communicator.send_json_to({
            'type': 'typing_stop'
        })

        # Connection should remain open
        await communicator.disconnect()

    @patch('websocket_server.consumers.ChatConsumer.get_user_from_token')
    @patch('websocket_server.consumers.ChatConsumer.verify_room_access')
    async def test_empty_message_handling(self, mock_verify_access, mock_get_user):
        """Test that empty messages are ignored."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send empty message
        await communicator.send_json_to({
            'type': 'chat_message',
            'message': '   '  # Only whitespace
        })

        # Should not receive any response
        await communicator.disconnect()

    @patch('websocket_server.consumers.ChatConsumer.get_user_from_token')
    @patch('websocket_server.consumers.ChatConsumer.verify_room_access')
    async def test_invalid_json_handling(self, mock_verify_access, mock_get_user):
        """Test invalid JSON handling."""
        mock_get_user.return_value = self.user
        mock_verify_access.return_value = True

        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.workspace.id}/workspace/{self.workspace.id}/?token={self.access_token}'
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send invalid JSON
        await communicator.send_to(text_data='invalid json')

        # Connection should remain open (error should be logged, not crash)
        await communicator.disconnect()


class WebSocketAuthenticationTest(TestCase):
    """Test WebSocket authentication helpers."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.access_token = str(AccessToken.for_user(self.user))

    def test_get_user_from_valid_token(self):
        """Test getting user from valid JWT token."""
        consumer = LiveUpdatesConsumer()
        consumer.scope = {
            'query_string': f'token={self.access_token}'.encode()
        }

        user = consumer.get_user_from_token_sync(self.access_token)
        self.assertEqual(user, self.user)

    def test_get_user_from_invalid_token(self):
        """Test getting user from invalid JWT token."""
        consumer = LiveUpdatesConsumer()
        consumer.scope = {
            'query_string': b'token=invalid-token'
        }

        user = consumer.get_user_from_token_sync('invalid-token')
        self.assertTrue(user.is_anonymous)

    def test_get_user_without_token(self):
        """Test getting user without token."""
        consumer = LiveUpdatesConsumer()
        consumer.scope = {
            'query_string': b''
        }

        user = consumer.get_user_from_token_sync(None)
        self.assertTrue(user.is_anonymous)

    def test_verify_workspace_access_with_membership(self):
        """Test workspace access verification with valid membership."""
        consumer = LiveUpdatesConsumer()
        consumer.user = self.user

        organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        workspace = Workspace.objects.create(
            organization=organization,
            name='Test Workspace'
        )

        Membership.objects.create(
            user=self.user,
            workspace=workspace,
            role='member'
        )

        consumer.workspace_id = str(workspace.id)
        has_access = consumer.verify_workspace_access()
        self.assertTrue(has_access)

    def test_verify_workspace_access_without_membership(self):
        """Test workspace access verification without membership."""
        consumer = LiveUpdatesConsumer()
        consumer.user = self.user

        organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        workspace = Workspace.objects.create(
            organization=organization,
            name='Test Workspace'
        )

        consumer.workspace_id = str(workspace.id)
        has_access = consumer.verify_workspace_access()
        self.assertFalse(has_access)