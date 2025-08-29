import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from chat.models import (
    ChatRoom, ChatMessage, ChatMention, ChatReaction,
    ChatRoomMembership, ChatNotification
)
from chat.serializers import (
    UserBasicSerializer, ChatReactionSerializer, ChatMentionSerializer,
    ChatMessageSerializer, ChatMessageCreateSerializer, ChatRoomMembershipSerializer,
    ChatRoomSerializer, ChatRoomCreateSerializer, ChatNotificationSerializer,
    ChatRoomListSerializer
)
from organizations.models import Organization, Workspace
import datetime

User = get_user_model()


class UserBasicSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_basic_serialization(self):
        """Test UserBasicSerializer serialization."""
        serializer = UserBasicSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['id'], str(self.user.id))
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['full_name'], 'Test User')


class ChatReactionSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message'
        )

        self.reaction = ChatReaction.objects.create(
            message=self.message,
            user=self.user,
            emoji='👍',
            emoji_name='thumbs_up'
        )

    def test_chat_reaction_serialization(self):
        """Test ChatReactionSerializer serialization."""
        serializer = ChatReactionSerializer(self.reaction)
        data = serializer.data

        self.assertEqual(data['emoji'], '👍')
        self.assertEqual(data['emoji_name'], 'thumbs_up')
        self.assertEqual(data['user']['email'], 'test@example.com')


class ChatMentionSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message'
        )

        self.mention = ChatMention.objects.create(
            message=self.message,
            user=self.user
        )

    def test_chat_mention_serialization(self):
        """Test ChatMentionSerializer serialization."""
        serializer = ChatMentionSerializer(self.mention)
        data = serializer.data

        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertFalse(data['is_read'])
        self.assertIsNone(data['read_at'])


class ChatMessageSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message',
            message_type='text'
        )

    def test_chat_message_serialization(self):
        """Test ChatMessageSerializer serialization."""
        serializer = ChatMessageSerializer(self.message)
        data = serializer.data

        self.assertEqual(data['content'], 'Test message')
        self.assertEqual(data['message_type'], 'text')
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['reply_count'], 0)

    def test_chat_message_with_mentions_creation(self):
        """Test creating message with mentions."""
        mention_user = User.objects.create_user(
            username='mentionuser',
            email='mention@example.com',
            password='testpass123'
        )

        data = {
            'room': str(self.room.id),
            'content': 'Test message with @mention',
            'message_type': 'text',
            'mention_user_ids': [str(mention_user.id)]
        }

        serializer = ChatMessageSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        message = serializer.save(user=self.user)

        self.assertEqual(message.content, 'Test message with @mention')
        self.assertEqual(message.mentions.count(), 1)
        self.assertEqual(message.mentions.first().user, mention_user)


class ChatMessageCreateSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

    def test_valid_message_creation(self):
        """Test creating valid message."""
        data = {
            'content': 'Valid message content',
            'message_type': 'text'
        }

        serializer = ChatMessageCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_content_validation(self):
        """Test empty content validation."""
        data = {
            'content': '   ',
            'message_type': 'text'
        }

        serializer = ChatMessageCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)

    def test_content_stripping(self):
        """Test content stripping."""
        data = {
            'content': '  Test message  ',
            'message_type': 'text'
        }

        serializer = ChatMessageCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['content'], 'Test message')


class ChatRoomMembershipSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.membership = ChatRoomMembership.objects.create(
            room=self.room,
            user=self.user,
            role='admin'
        )

    def test_chat_room_membership_serialization(self):
        """Test ChatRoomMembershipSerializer serialization."""
        serializer = ChatRoomMembershipSerializer(self.membership)
        data = serializer.data

        self.assertEqual(data['role'], 'admin')
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['unread_count'], 0)


class ChatRoomSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            description='Test Description',
            created_by=self.user
        )

        # Add membership
        ChatRoomMembership.objects.create(
            room=self.room,
            user=self.user,
            role='admin'
        )

        # Add a message
        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message content'
        )

    def test_chat_room_serialization(self):
        """Test ChatRoomSerializer serialization."""
        serializer = ChatRoomSerializer(self.room)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Room')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['room_type'], 'channel')
        self.assertEqual(data['member_count'], 1)
        self.assertEqual(data['message_count'], 1)
        self.assertIsNotNone(data['last_message_preview'])


class ChatRoomCreateSerializerTest(TestCase):
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

    def test_chat_room_creation_with_members(self):
        """Test creating room with initial members."""
        member_user = User.objects.create_user(
            username='memberuser',
            email='member@example.com',
            password='testpass123'
        )

        data = {
            'room_type': 'channel',
            'workspace': str(self.workspace.id),
            'name': 'New Room',
            'description': 'New room description',
            'is_private': False,
            'initial_members': [str(member_user.id)]
        }

        serializer = ChatRoomCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        room = serializer.save(created_by=self.user)

        self.assertEqual(room.name, 'New Room')
        self.assertEqual(room.memberships.count(), 2)  # Creator + member
        self.assertTrue(room.memberships.filter(user=self.user, role='admin').exists())
        self.assertTrue(room.memberships.filter(user=member_user, role='member').exists())


class ChatNotificationSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        self.message = ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='Test message'
        )

        self.notification = ChatNotification.objects.create(
            notification_type='mention',
            title='You were mentioned',
            content='Test mention notification',
            room=self.room,
            message=self.message
        )

    def test_chat_notification_serialization(self):
        """Test ChatNotificationSerializer serialization."""
        serializer = ChatNotificationSerializer(self.notification)
        data = serializer.data

        self.assertEqual(data['notification_type'], 'mention')
        self.assertEqual(data['title'], 'You were mentioned')
        self.assertEqual(data['content'], 'Test mention notification')
        self.assertEqual(data['room']['name'], 'Test Room')
        self.assertEqual(data['message']['content'], 'Test message')


class ChatRoomListSerializerTest(TestCase):
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

        self.room = ChatRoom.objects.create(
            room_type='channel',
            workspace=self.workspace,
            name='Test Room',
            created_by=self.user
        )

        # Add membership
        ChatRoomMembership.objects.create(
            room=self.room,
            user=self.user,
            role='member'
        )

        # Add a message
        ChatMessage.objects.create(
            room=self.room,
            user=self.user,
            content='This is a longer message that should be truncated in preview'
        )

    def test_chat_room_list_serialization(self):
        """Test ChatRoomListSerializer serialization."""
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user

        serializer = ChatRoomListSerializer(self.room, context={'request': request})
        data = serializer.data

        self.assertEqual(data['name'], 'Test Room')
        self.assertEqual(data['room_type'], 'channel')
        self.assertEqual(data['member_count'], 1)
        self.assertEqual(data['unread_count'], 0)
        self.assertIsNotNone(data['last_message_preview'])
        self.assertTrue(data['last_message_preview']['content'].endswith('...'))