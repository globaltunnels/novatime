import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from chat.models import ChatMessage, ChatMention, ChatReaction
from chat.signals import (
    handle_new_chat_message,
    handle_chat_mention,
    handle_chat_reaction
)
from organizations.models import Organization, Workspace
import datetime

User = get_user_model()


class ChatSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.room = ChatMessage.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message content',
            message_type='text'
        )

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_new_chat_message_broadcast(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that new chat messages are broadcast to room and workspace groups."""
        # Setup mocks
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a new message (trigger signal)
        new_message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='New test message',
            message_type='text'
        )

        # Verify room group message
        expected_room_group = f"chat_{self.room.room_type}_{self.room.room_id}"
        expected_workspace_group = f"workspace_{self.workspace.id}"

        # Check that group_send was called for room
        room_calls = [call for call in mock_group_send.call_args_list
                     if call[0][0] == expected_room_group]
        self.assertEqual(len(room_calls), 1)

        room_message = room_calls[0][0][1]
        self.assertEqual(room_message['type'], 'chat_message_broadcast')
        self.assertEqual(room_message['message']['content'], 'New test message')
        self.assertEqual(room_message['message']['user_name'], 'Test User')

        # Check that group_send was called for workspace
        workspace_calls = [call for call in mock_group_send.call_args_list
                          if call[0][0] == expected_workspace_group]
        self.assertEqual(len(workspace_calls), 1)

        workspace_message = workspace_calls[0][0][1]
        self.assertEqual(workspace_message['type'], 'workspace_update')
        self.assertEqual(workspace_message['event_type'], 'new_chat_message')

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_new_chat_message_deleted_ignored(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that deleted messages don't trigger broadcasts."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a deleted message
        deleted_message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Deleted message',
            message_type='text',
            is_deleted=True
        )

        # Verify no broadcasts occurred
        mock_group_send.assert_not_called()

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_chat_mention_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that mentions trigger user notifications."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a mention
        mention = ChatMention.objects.create(
            message=self.message,
            user=self.other_user
        )

        # Verify user notification was sent
        expected_user_group = f"user_{self.other_user.id}"
        calls = [call for call in mock_group_send.call_args_list
                if call[0][0] == expected_user_group]
        self.assertEqual(len(calls), 1)

        notification = calls[0][0][1]
        self.assertEqual(notification['type'], 'user_notification')
        self.assertEqual(notification['notification_type'], 'chat_mention')
        self.assertIn('You were mentioned in', notification['message'])
        self.assertEqual(notification['data']['message_id'], str(self.message.id))

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_chat_reaction_broadcast(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that reactions are broadcast to room group."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a reaction
        reaction = ChatReaction.objects.create(
            message=self.message,
            user=self.other_user,
            emoji='👍',
            emoji_name='thumbs_up'
        )

        # Verify room broadcast
        expected_room_group = f"chat_{self.room.room_type}_{self.room.room_id}"
        calls = [call for call in mock_group_send.call_args_list
                if call[0][0] == expected_room_group]
        self.assertEqual(len(calls), 1)

        reaction_message = calls[0][0][1]
        self.assertEqual(reaction_message['type'], 'chat_reaction')
        self.assertEqual(reaction_message['message_id'], str(self.message.id))
        self.assertEqual(reaction_message['reaction']['emoji'], '👍')

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_chat_reaction_author_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that message authors get notified of reactions from others."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a reaction from different user
        reaction = ChatReaction.objects.create(
            message=self.message,
            user=self.other_user,
            emoji='❤️',
            emoji_name='heart'
        )

        # Verify author notification
        expected_user_group = f"user_{self.user.id}"
        user_calls = [call for call in mock_group_send.call_args_list
                     if call[0][0] == expected_user_group]
        self.assertEqual(len(user_calls), 1)

        notification = user_calls[0][0][1]
        self.assertEqual(notification['type'], 'user_notification')
        self.assertEqual(notification['notification_type'], 'chat_reaction')
        self.assertIn('reacted ❤️ to your message', notification['message'])

    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_chat_reaction_self_no_notification(self, mock_get_channel_layer, mock_async_to_sync):
        """Test that users don't get notified of their own reactions."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_group_send = MagicMock()
        mock_async_to_sync.return_value = mock_group_send

        # Create a self-reaction
        reaction = ChatReaction.objects.create(
            message=self.message,
            user=self.user,  # Same as message author
            emoji='👍',
            emoji_name='thumbs_up'
        )

        # Verify no user notification was sent
        expected_user_group = f"user_{self.user.id}"
        user_calls = [call for call in mock_group_send.call_args_list
                     if call[0][0] == expected_user_group]
        self.assertEqual(len(user_calls), 0)

    @patch('chat.signals.logger')
    @patch('chat.signals.async_to_sync')
    @patch('chat.signals.get_channel_layer')
    def test_handle_signals_exception_handling(self, mock_get_channel_layer, mock_async_to_sync, mock_logger):
        """Test that exceptions in signal handlers are logged."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.side_effect = Exception("WebSocket error")

        # Create a message (should trigger exception in signal)
        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message',
            message_type='text'
        )

        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        self.assertIn("Error broadcasting chat message", error_message)