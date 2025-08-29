from django.db import models
from django.utils import timezone
from django.core.validators import MaxLengthValidator
import uuid


def default_dict():
    """Default empty dictionary"""
    return {}


class ChatRoom(models.Model):
    """
    Chat rooms for different types of conversations.
    """
    ROOM_TYPES = [
        ('workspace', 'Workspace'),
        ('project', 'Project'),
        ('direct', 'Direct Message'),
        ('team', 'Team'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Room identification
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    room_id = models.CharField(max_length=255)  # References workspace_id, project_id, etc.
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )
    
    # Room details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last activity tracking
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_chat_rooms'
    )
    
    class Meta:
        db_table = 'chat_rooms'
        unique_together = ['room_type', 'room_id', 'workspace']
        indexes = [
            models.Index(fields=['workspace', 'room_type']),
            models.Index(fields=['last_message_at']),
        ]
    
    def __str__(self):
        return f"{self.get_room_type_display()}: {self.name}"


class ChatMessage(models.Model):
    """
    Individual chat messages within rooms.
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('system', 'System'),
        ('mention', 'Mention'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Message context
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(validators=[MaxLengthValidator(4000)])
    formatted_content = models.TextField(blank=True)  # HTML formatted content
    
    # File attachments
    attachment_url = models.URLField(blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)  # bytes
    attachment_type = models.CharField(max_length=100, blank=True)  # MIME type
    
    # Message features
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Thread support
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    thread_count = models.PositiveIntegerField(default=0)
    
    # Mentions and reactions
    mentions = models.ManyToManyField(
        'iam.User',
        through='ChatMention',
        related_name='mentioned_in_chats'
    )
    
    # Metadata
    metadata = models.JSONField(default=default_dict)  # Additional message data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['parent_message']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.user.email}: {content_preview}"
    
    def save(self, *args, **kwargs):
        """Update room's last message info when saving."""
        super().save(*args, **kwargs)
        
        # Update room's last message tracking
        if not self.is_deleted:
            self.room.last_message_at = self.created_at
            self.room.last_message_by = self.user
            self.room.save(update_fields=['last_message_at', 'last_message_by'])


class ChatMention(models.Model):
    """
    User mentions in chat messages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='mention_records'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='chat_mention_records'
    )
    
    # Mention tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_mentions'
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.email} mentioned in {self.message.id}"


class ChatReaction(models.Model):
    """
    Emoji reactions to chat messages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='chat_reactions'
    )
    
    # Reaction details
    emoji = models.CharField(max_length=10)  # Unicode emoji
    emoji_name = models.CharField(max_length=50)  # e.g., 'thumbs_up', 'heart'
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_reactions'
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'emoji']),
        ]
    
    def __str__(self):
        return f"{self.user.email} reacted {self.emoji} to {self.message.id}"


class ChatRoomMembership(models.Model):
    """
    User membership in chat rooms (for private rooms and permissions).
    """
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='chat_room_memberships'
    )
    
    # Membership details
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    can_post = models.BooleanField(default=True)
    can_invite = models.BooleanField(default=False)
    
    # Notification preferences
    notifications_enabled = models.BooleanField(default=True)
    mention_notifications = models.BooleanField(default=True)
    
    # Activity tracking
    last_read_at = models.DateTimeField(null=True, blank=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_room_memberships'
        unique_together = ['room', 'user']
        indexes = [
            models.Index(fields=['user', 'last_read_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} in {self.room.name} ({self.role})"


class ChatNotification(models.Model):
    """
    Chat-related notifications for users.
    """
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('mention', 'Mentioned'),
        ('reaction', 'Reaction'),
        ('thread_reply', 'Thread Reply'),
        ('room_invite', 'Room Invitation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='chat_notifications'
    )
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['room', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.email}"