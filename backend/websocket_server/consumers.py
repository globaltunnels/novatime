import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()
logger = logging.getLogger(__name__)


class LiveUpdatesConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time live updates across the application.
    Handles notifications, timesheet updates, project updates, etc.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Get user from token authentication
        user = await self.get_user_from_token()
        if not user or user.is_anonymous:
            await self.close()
            return
        
        self.user = user
        self.workspace_id = self.scope['url_route']['kwargs'].get('workspace_id')
        
        if not self.workspace_id:
            await self.close()
            return
        
        # Verify user has access to workspace
        has_access = await self.verify_workspace_access()
        if not has_access:
            await self.close()
            return
        
        # Join workspace group for real-time updates
        self.workspace_group_name = f"workspace_{self.workspace_id}"
        await self.channel_layer.group_add(
            self.workspace_group_name,
            self.channel_name
        )
        
        # Join user-specific group for personal notifications
        self.user_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected: user={user.email}, workspace={self.workspace_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'workspace_group_name'):
            await self.channel_layer.group_discard(
                self.workspace_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected: close_code={close_code}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'subscribe':
                # Subscribe to specific channels (e.g., project updates, timesheet changes)
                channels = data.get('channels', [])
                await self.handle_subscription(channels)
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def handle_subscription(self, channels):
        """Handle subscription to specific update channels."""
        for channel in channels:
            if channel.startswith('project_'):
                project_id = channel.split('_')[1]
                # Verify user has access to project
                has_access = await self.verify_project_access(project_id)
                if has_access:
                    group_name = f"project_{project_id}"
                    await self.channel_layer.group_add(group_name, self.channel_name)
            
            elif channel.startswith('timesheet_'):
                # Handle timesheet subscriptions
                group_name = f"timesheet_updates_{self.workspace_id}"
                await self.channel_layer.group_add(group_name, self.channel_name)
    
    # Group message handlers
    async def workspace_update(self, event):
        """Send workspace update to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def user_notification(self, event):
        """Send user notification to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def project_update(self, event):
        """Send project update to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def timesheet_update(self, event):
        """Send timesheet update to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def time_entry_update(self, event):
        """Send time entry update to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    # Authentication and authorization helpers
    async def get_user_from_token(self):
        """Get user from JWT token in query string."""
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            return AnonymousUser()
        
        try:
            # Validate JWT token
            UntypedToken(token)
            user = await self.get_user_from_token_sync(token)
            return user
        except (InvalidToken, TokenError, Exception):
            return AnonymousUser()
    
    @database_sync_to_async
    def get_user_from_token_sync(self, token):
        """Synchronous helper to get user from token."""
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()
    
    @database_sync_to_async
    def verify_workspace_access(self):
        """Verify user has access to workspace."""
        from organizations.models import Membership
        try:
            Membership.objects.get(
                user=self.user,
                workspace_id=self.workspace_id,
                is_active=True
            )
            return True
        except Membership.DoesNotExist:
            return False
    
    @database_sync_to_async
    def verify_project_access(self, project_id):
        """Verify user has access to project."""
        from projects.models import Project, ProjectMember
        try:
            # Check if user is project member or has workspace access
            project = Project.objects.get(id=project_id)
            if project.workspace_id == self.workspace_id:
                return True
            
            # Or check if user is project member
            ProjectMember.objects.get(project_id=project_id, user=self.user)
            return True
        except (Project.DoesNotExist, ProjectMember.DoesNotExist):
            return False


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat functionality.
    Handles project discussions, team communication, etc.
    """
    
    async def connect(self):
        """Handle WebSocket connection for chat."""
        # Get user from token authentication
        user = await self.get_user_from_token()
        if not user or user.is_anonymous:
            await self.close()
            return
        
        self.user = user
        self.workspace_id = self.scope['url_route']['kwargs'].get('workspace_id')
        self.room_type = self.scope['url_route']['kwargs'].get('room_type')  # 'workspace', 'project', 'direct'
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        
        if not all([self.workspace_id, self.room_type, self.room_id]):
            await self.close()
            return
        
        # Verify access based on room type
        has_access = await self.verify_room_access()
        if not has_access:
            await self.close()
            return
        
        # Join chat room group
        self.room_group_name = f"chat_{self.room_type}_{self.room_id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Chat connected: user={user.email}, room={self.room_group_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection for chat."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"Chat disconnected: close_code={close_code}")
    
    async def receive(self, text_data):
        """Handle chat messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_indicator(data, True)
            elif message_type == 'typing_stop':
                await self.handle_typing_indicator(data, False)
            else:
                logger.warning(f"Unknown chat message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in chat")
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message."""
        message_content = data.get('message', '').strip()
        if not message_content:
            return
        
        # Save message to database
        message = await self.save_chat_message(message_content)
        if not message:
            return
        
        # Broadcast message to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_broadcast',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'user_id': str(message.user.id),
                    'user_name': message.user.get_full_name() or message.user.email,
                    'user_avatar': message.user.avatar_url,
                    'timestamp': message.created_at.isoformat(),
                    'room_type': self.room_type,
                    'room_id': self.room_id
                }
            }
        )
    
    async def handle_typing_indicator(self, data, is_typing):
        """Handle typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'user_name': self.user.get_full_name() or self.user.email,
                'is_typing': is_typing
            }
        )
    
    # Group message handlers
    async def chat_message_broadcast(self, event):
        """Broadcast chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator to the sender
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    # Database operations
    @database_sync_to_async
    def save_chat_message(self, content):
        """Save chat message to database."""
        from chat.models import ChatMessage, ChatRoom
        try:
            # Get or create chat room
            room, created = ChatRoom.objects.get_or_create(
                room_type=self.room_type,
                room_id=self.room_id,
                workspace_id=self.workspace_id,
                defaults={
                    'name': f"{self.room_type.title()} {self.room_id}",
                    'created_by': self.user
                }
            )
            
            # Create message
            message = ChatMessage.objects.create(
                room=room,
                user=self.user,
                content=content
            )
            
            return message
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return None
    
    # Authentication and authorization helpers (same as LiveUpdatesConsumer)
    async def get_user_from_token(self):
        """Get user from JWT token in query string."""
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            return AnonymousUser()
        
        try:
            UntypedToken(token)
            user = await self.get_user_from_token_sync(token)
            return user
        except (InvalidToken, TokenError, Exception):
            return AnonymousUser()
    
    @database_sync_to_async
    def get_user_from_token_sync(self, token):
        """Synchronous helper to get user from token."""
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()
    
    @database_sync_to_async
    def verify_room_access(self):
        """Verify user has access to chat room."""
        from organizations.models import Membership
        from projects.models import Project, ProjectMember
        
        try:
            # Verify workspace access first
            Membership.objects.get(
                user=self.user,
                workspace_id=self.workspace_id,
                is_active=True
            )
            
            # Additional checks based on room type
            if self.room_type == 'project':
                # Verify project access
                try:
                    project = Project.objects.get(id=self.room_id)
                    if project.workspace_id == self.workspace_id:
                        return True
                    
                    # Or check if user is project member
                    ProjectMember.objects.get(project_id=self.room_id, user=self.user)
                    return True
                except (Project.DoesNotExist, ProjectMember.DoesNotExist):
                    return False
            
            elif self.room_type == 'workspace':
                # Already verified workspace access above
                return self.room_id == self.workspace_id
            
            elif self.room_type == 'direct':
                # For direct messages, verify both users have workspace access
                # room_id format: "user1_id__user2_id"
                user_ids = self.room_id.split('__')
                if str(self.user.id) not in user_ids:
                    return False
                
                # Verify other user also has workspace access
                other_user_id = user_ids[0] if user_ids[1] == str(self.user.id) else user_ids[1]
                Membership.objects.get(
                    user_id=other_user_id,
                    workspace_id=self.workspace_id,
                    is_active=True
                )
                return True
            
            return True
            
        except Membership.DoesNotExist:
            return False
        except Exception:
            return False