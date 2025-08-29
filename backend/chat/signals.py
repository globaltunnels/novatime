from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatMessage, ChatMention, ChatReaction
import logging

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=ChatMessage)
def handle_new_chat_message(sender, instance, created, **kwargs):
    """Handle new chat message for real-time broadcasting."""
    if not created or instance.is_deleted:
        return
    
    try:
        # Broadcast to room group
        room_group = f"chat_{instance.room.room_type}_{instance.room.room_id}"
        
        message_data = {
            'type': 'chat_message_broadcast',
            'message': {
                'id': str(instance.id),
                'content': instance.content,
                'user_id': str(instance.user.id),
                'user_name': instance.user.get_full_name() or instance.user.email,
                'user_avatar': instance.user.avatar_url,
                'timestamp': instance.created_at.isoformat(),
                'room_type': instance.room.room_type,
                'room_id': instance.room.room_id,
                'message_type': instance.message_type,
                'parent_message_id': str(instance.parent_message.id) if instance.parent_message else None
            }
        }
        
        async_to_sync(channel_layer.group_send)(room_group, message_data)
        
        # Also send to workspace live updates
        workspace_group = f"workspace_{instance.room.workspace.id}"
        workspace_data = {
            'type': 'workspace_update',
            'event_type': 'new_chat_message',
            'data': message_data['message']
        }
        
        async_to_sync(channel_layer.group_send)(workspace_group, workspace_data)
        
    except Exception as e:
        logger.error(f"Error broadcasting chat message: {e}")


@receiver(post_save, sender=ChatMention)
def handle_chat_mention(sender, instance, created, **kwargs):
    """Handle chat mentions for notifications."""
    if not created:
        return
    
    try:
        # Send notification to mentioned user
        user_group = f"user_{instance.user.id}"
        
        notification_data = {
            'type': 'user_notification',
            'notification_type': 'chat_mention',
            'message': f"You were mentioned in {instance.message.room.name}",
            'data': {
                'message_id': str(instance.message.id),
                'room_id': str(instance.message.room.id),
                'room_name': instance.message.room.name,
                'from_user': instance.message.user.get_full_name() or instance.message.user.email,
                'content_preview': instance.message.content[:100]
            },
            'timestamp': instance.created_at.isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(user_group, notification_data)
        
    except Exception as e:
        logger.error(f"Error handling chat mention: {e}")


@receiver(post_save, sender=ChatReaction)
def handle_chat_reaction(sender, instance, created, **kwargs):
    """Handle chat reactions for real-time updates."""
    if not created:
        return
    
    try:
        # Broadcast reaction to room
        room_group = f"chat_{instance.message.room.room_type}_{instance.message.room.room_id}"
        
        reaction_data = {
            'type': 'chat_reaction',
            'message_id': str(instance.message.id),
            'reaction': {
                'id': str(instance.id),
                'emoji': instance.emoji,
                'emoji_name': instance.emoji_name,
                'user_id': str(instance.user.id),
                'user_name': instance.user.get_full_name() or instance.user.email
            },
            'timestamp': instance.created_at.isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(room_group, reaction_data)
        
        # Notify message author if it's not their own reaction
        if instance.user != instance.message.user:
            user_group = f"user_{instance.message.user.id}"
            notification_data = {
                'type': 'user_notification',
                'notification_type': 'chat_reaction',
                'message': f"{instance.user.get_full_name() or instance.user.email} reacted {instance.emoji} to your message",
                'data': {
                    'message_id': str(instance.message.id),
                    'reaction': reaction_data['reaction']
                },
                'timestamp': instance.created_at.isoformat()
            }
            
            async_to_sync(channel_layer.group_send)(user_group, notification_data)
        
    except Exception as e:
        logger.error(f"Error handling chat reaction: {e}")