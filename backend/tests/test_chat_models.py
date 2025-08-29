import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from chat.models import ChatMessage, ChatRoom, ChatRoomMembership

User = get_user_model()


class ChatMessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.room = ChatRoom.objects.create(
            room_type='direct',
            room_id='test-room-123',
            name='Test Room'
        )
        
    def test_chat_message_creation(self):
        message = ChatMessage.objects.create(
            room=self.room,
            sender=self.user,
            content='Hello, test message!'
        )
        
        self.assertEqual(message.room, self.room)
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.content, 'Hello, test message!')
        self.assertFalse(message.is_edited)
        self.assertIsNotNone(message.timestamp)
        
    def test_chat_message_string_representation(self):
        message = ChatMessage.objects.create(
            room=self.room,
            sender=self.user,
            content='Test message'
        )
        
        expected_str = f"From {self.user.username} in {self.room.name}: Test message"
        self.assertEqual(str(message), expected_str)


class ChatRoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_chat_room_creation(self):
        room = ChatRoom.objects.create(
            room_type='direct',
            room_id='test-room-123',
            name='Test Room',
            description='A test chat room'
        )
        
        self.assertEqual(room.room_type, 'direct')
        self.assertEqual(room.room_id, 'test-room-123')
        self.assertEqual(room.name, 'Test Room')
        self.assertEqual(room.description, 'A test chat room')
        self.assertFalse(room.is_private)
        self.assertFalse(room.is_archived)
        self.assertIsNotNone(room.created_at)
        self.assertIsNotNone(room.updated_at)
        
    def test_chat_room_string_representation(self):
        room = ChatRoom.objects.create(
            room_type='direct',
            room_id='test-room-123',
            name='Test Room'
        )
        
        self.assertEqual(str(room), 'Test Room (direct)')


class ChatRoomMembershipModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.room = ChatRoom.objects.create(
            room_type='direct',
            room_id='test-room-123',
            name='Test Room'
        )
        
    def test_chat_room_membership_creation(self):
        membership = ChatRoomMembership.objects.create(
            room=self.room,
            user=self.user,
            role='member'
        )
        
        self.assertEqual(membership.room, self.room)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, 'member')
        self.assertTrue(membership.is_active)
        self.assertIsNotNone(membership.joined_at)
        
    def test_chat_room_membership_string_representation(self):
        membership = ChatRoomMembership.objects.create(
            room=self.room,
            user=self.user,
            role='admin'
        )
        
        expected_str = f"{self.user.username} in {self.room.name} ({membership.role})"
        self.assertEqual(str(membership), expected_str)