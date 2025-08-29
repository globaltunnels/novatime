from rest_framework import serializers
from django.utils import timezone
from .models import (
    ChatRoom, ChatMessage, ChatMention, ChatReaction,
    ChatRoomMembership, ChatNotification
)
from iam.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for chat contexts."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'avatar_url']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'avatar_url']


class ChatReactionSerializer(serializers.ModelSerializer):
    """Serializer for message reactions."""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChatReaction
        fields = ['id', 'emoji', 'emoji_name', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatMentionSerializer(serializers.ModelSerializer):
    """Serializer for message mentions."""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChatMention
        fields = ['id', 'user', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    
    user = UserBasicSerializer(read_only=True)
    mentions = ChatMentionSerializer(source='mention_records', many=True, read_only=True)
    reactions = ChatReactionSerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    # For creating messages with mentions
    mention_user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'user', 'message_type', 'content', 'formatted_content',
            'attachment_url', 'attachment_name', 'attachment_size', 'attachment_type',
            'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'parent_message', 'thread_count', 'reply_count',
            'mentions', 'reactions', 'mention_user_ids',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'thread_count', 'reply_count', 'mentions', 'reactions',
            'created_at', 'updated_at'
        ]
    
    def get_reply_count(self, obj):
        """Get number of replies to this message."""
        return obj.replies.filter(is_deleted=False).count()
    
    def create(self, validated_data):
        """Create message with mentions."""
        mention_user_ids = validated_data.pop('mention_user_ids', [])
        message = super().create(validated_data)
        
        # Create mentions
        for user_id in mention_user_ids:
            try:
                user = User.objects.get(id=user_id)
                ChatMention.objects.create(message=message, user=user)
            except User.DoesNotExist:
                continue
        
        return message


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating messages."""
    
    mention_user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = ChatMessage
        fields = [
            'content', 'message_type', 'parent_message',
            'attachment_url', 'attachment_name', 'attachment_size', 'attachment_type',
            'mention_user_ids'
        ]
    
    def validate_content(self, value):
        """Validate message content."""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class ChatRoomMembershipSerializer(serializers.ModelSerializer):
    """Serializer for room memberships."""
    
    user = UserBasicSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoomMembership
        fields = [
            'id', 'user', 'role', 'can_post', 'can_invite',
            'notifications_enabled', 'mention_notifications',
            'last_read_at', 'last_active_at', 'unread_count', 'joined_at'
        ]
        read_only_fields = ['id', 'user', 'unread_count', 'joined_at']
    
    def get_unread_count(self, obj):
        """Get unread message count for this user in the room."""
        last_read = obj.last_read_at or obj.joined_at
        return obj.room.messages.filter(
            created_at__gt=last_read,
            is_deleted=False
        ).exclude(user=obj.user).count()


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms."""
    
    created_by = UserBasicSerializer(read_only=True)
    last_message_by = UserBasicSerializer(read_only=True)
    memberships = ChatRoomMembershipSerializer(many=True, read_only=True)
    
    # Statistics
    member_count = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'room_id', 'workspace', 'name', 'description',
            'is_private', 'is_archived', 'created_by', 'created_at', 'updated_at',
            'last_message_at', 'last_message_by', 'last_message_preview',
            'member_count', 'message_count', 'memberships'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'last_message_at', 'last_message_by', 'last_message_preview',
            'member_count', 'message_count', 'memberships'
        ]
    
    def get_member_count(self, obj):
        """Get number of room members."""
        return obj.memberships.count()
    
    def get_message_count(self, obj):
        """Get total message count."""
        return obj.messages.filter(is_deleted=False).count()
    
    def get_last_message_preview(self, obj):
        """Get preview of last message."""
        last_message = obj.messages.filter(is_deleted=False).first()
        if last_message:
            content = last_message.content
            if len(content) > 100:
                content = content[:100] + '...'
            return {
                'id': str(last_message.id),
                'content': content,
                'user_name': last_message.user.get_full_name() or last_message.user.email,
                'created_at': last_message.created_at
            }
        return None


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms."""
    
    initial_members = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = ChatRoom
        fields = [
            'room_type', 'room_id', 'workspace', 'name', 'description',
            'is_private', 'initial_members'
        ]
    
    def create(self, validated_data):
        """Create room with initial members."""
        initial_members = validated_data.pop('initial_members', [])
        room = super().create(validated_data)
        
        # Add initial members
        for user_id in initial_members:
            try:
                user = User.objects.get(id=user_id)
                ChatRoomMembership.objects.create(
                    room=room,
                    user=user,
                    role='member'
                )
            except User.DoesNotExist:
                continue
        
        # Add creator as admin
        if room.created_by:
            ChatRoomMembership.objects.get_or_create(
                room=room,
                user=room.created_by,
                defaults={'role': 'admin'}
            )
        
        return room


class ChatNotificationSerializer(serializers.ModelSerializer):
    """Serializer for chat notifications."""
    
    room = ChatRoomSerializer(read_only=True)
    message = ChatMessageSerializer(read_only=True)
    
    class Meta:
        model = ChatNotification
        fields = [
            'id', 'notification_type', 'title', 'content',
            'room', 'message', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'room', 'message', 'created_at']


class ChatRoomListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for room lists."""
    
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'room_id', 'name', 'is_private', 'is_archived',
            'last_message_at', 'last_message_preview', 'unread_count', 'member_count'
        ]
    
    def get_last_message_preview(self, obj):
        """Get preview of last message."""
        last_message = obj.messages.filter(is_deleted=False).first()
        if last_message:
            return {
                'content': last_message.content[:50] + ('...' if len(last_message.content) > 50 else ''),
                'user_name': last_message.user.get_full_name() or last_message.user.email,
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        """Get unread count for current user."""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user:
            return 0
        
        try:
            membership = obj.memberships.get(user=user)
            last_read = membership.last_read_at or membership.joined_at
            return obj.messages.filter(
                created_at__gt=last_read,
                is_deleted=False
            ).exclude(user=user).count()
        except ChatRoomMembership.DoesNotExist:
            return 0
    
    def get_member_count(self, obj):
        """Get member count."""
        return obj.memberships.count()