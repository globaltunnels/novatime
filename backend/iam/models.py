from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


def default_list():
    """Default empty list"""
    return []


def default_dict():
    """Default empty dictionary"""
    return {}


class User(AbstractUser):
    """
    Extended User model with additional fields for NovaTime.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    avatar_url = models.URLField(blank=True)
    user_timezone = models.CharField(max_length=50, default='UTC')
    is_email_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # OIDC/OAuth fields
    oidc_subject = models.CharField(max_length=255, blank=True, null=True, unique=True)
    provider = models.CharField(max_length=50, blank=True)  # google, github, etc.
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    theme_preference = models.CharField(
        max_length=10, 
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='auto'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return self.email


class Role(models.Model):
    """
    Role-based access control roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=default_list)  # List of permission strings
    is_system_role = models.BooleanField(default=False)  # Predefined system roles
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        
    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    User-to-Role assignment with organization context.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255, blank=True)  # Temporarily as string
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='granted_roles'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"


class Session(models.Model):
    """
    Enhanced session tracking for security monitoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=255, blank=True)  # Geo location
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class AuditLog(models.Model):
    """
    Audit trail for security and compliance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)  # login, logout, create, update, delete
    resource_type = models.CharField(max_length=100)  # User, Task, TimeEntry, etc.
    resource_id = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)  # Temporarily as string
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=default_dict)  # Additional context
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
        
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
