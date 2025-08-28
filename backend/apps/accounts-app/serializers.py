"""
Serializers for accounts app.

This module contains serializers for User, UserProfile, UserSession,
PasswordResetToken, EmailVerificationToken, and UserActivity models
for API serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from datetime import timedelta

from .models import (
    User, UserProfile, UserSession, PasswordResetToken,
    EmailVerificationToken, UserActivity
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    full_name = serializers.CharField(
        source='get_full_name',
        read_only=True
    )
    profile_completion = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    organizations_count = serializers.SerializerMethodField()
    workspaces_count = serializers.SerializerMethodField()
    teams_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'avatar_url', 'bio', 'title', 'department', 'phone',
            'timezone', 'language', 'work_hours_start', 'work_hours_end',
            'work_days', 'email_notifications', 'push_notifications',
            'weekly_digest', 'profile_visibility', 'show_online_status',
            'two_factor_enabled', 'passkeys_enabled', 'is_active',
            'is_verified', 'profile_completion', 'is_online',
            'organizations_count', 'workspaces_count', 'teams_count',
            'created_at', 'updated_at', 'last_login_at', 'last_activity_at'
        ]
        read_only_fields = [
            'id', 'profile_completion', 'is_online', 'organizations_count',
            'workspaces_count', 'teams_count', 'created_at', 'updated_at',
            'last_login_at', 'last_activity_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_profile_completion(self, obj):
        """Get profile completion percentage."""
        return obj.get_profile_completion_percentage()

    def get_is_online(self, obj):
        """Check if user is online."""
        return obj.is_online()

    def get_organizations_count(self, obj):
        """Get organizations count."""
        return obj.get_organizations().count()

    def get_workspaces_count(self, obj):
        """Get workspaces count."""
        return obj.get_workspaces().count()

    def get_teams_count(self, obj):
        """Get teams count."""
        return obj.get_teams().count()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'password_confirm'
        ]

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value

    def validate(self, data):
        """Validate passwords match."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                _("Passwords do not match.")
            )
        return data

    def create(self, validated_data):
        """Create user."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar_url', 'bio', 'title',
            'department', 'phone', 'timezone', 'language', 'work_hours_start',
            'work_hours_end', 'work_days', 'email_notifications',
            'push_notifications', 'weekly_digest', 'profile_visibility',
            'show_online_status'
        ]

    def validate_work_days(self, value):
        """Validate work days."""
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in value:
            if day not in valid_days:
                raise serializers.ValidationError(
                    _("Invalid day: %(day)s") % {'day': day}
                )
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_name', 'date_of_birth', 'gender', 'location',
            'years_of_experience', 'skills', 'certifications', 'linkedin_url',
            'github_url', 'twitter_handle', 'website_url', 'theme',
            'date_format', 'time_format', 'currency', 'work_style',
            'meeting_availability', 'notification_preferences', 'data_sharing',
            'marketing_emails', 'completion_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completion_percentage', 'created_at', 'updated_at']

    def get_completion_percentage(self, obj):
        """Get profile completion percentage."""
        return obj.get_completion_percentage()


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user profiles."""

    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 'gender', 'location', 'years_of_experience',
            'skills', 'certifications', 'linkedin_url', 'github_url',
            'twitter_handle', 'website_url', 'theme', 'date_format',
            'time_format', 'currency', 'work_style', 'meeting_availability',
            'notification_preferences', 'data_sharing', 'marketing_emails'
        ]


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_name', 'session_key', 'device_type',
            'device_name', 'browser', 'ip_address', 'user_agent',
            'location', 'is_active', 'is_expired', 'is_online',
            'created_at', 'last_activity_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'session_key', 'is_expired', 'is_online', 'created_at'
        ]

    def get_is_expired(self, obj):
        """Check if session is expired."""
        return obj.is_expired()

    def get_is_online(self, obj):
        """Check if session is online."""
        return not obj.is_expired() and obj.is_active


class PasswordResetTokenSerializer(serializers.ModelSerializer):
    """Serializer for PasswordResetToken model."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = PasswordResetToken
        fields = [
            'id', 'user', 'user_email', 'token', 'is_used', 'is_expired',
            'created_at', 'expires_at', 'used_at'
        ]
        read_only_fields = [
            'id', 'token', 'is_expired', 'created_at', 'used_at'
        ]

    def get_is_expired(self, obj):
        """Check if token is expired."""
        return obj.is_expired()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset requests."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("No active user found with this email address.")
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""

    token = serializers.CharField()
    password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate passwords match."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                _("Passwords do not match.")
            )
        return data


class EmailVerificationTokenSerializer(serializers.ModelSerializer):
    """Serializer for EmailVerificationToken model."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = EmailVerificationToken
        fields = [
            'id', 'user', 'user_email', 'token', 'email', 'is_verified',
            'is_expired', 'created_at', 'expires_at', 'verified_at'
        ]
        read_only_fields = [
            'id', 'token', 'is_expired', 'created_at', 'verified_at'
        ]

    def get_is_expired(self, obj):
        """Check if token is expired."""
        return obj.is_expired()


class EmailVerificationRequestSerializer(serializers.Serializer):
    """Serializer for email verification requests."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email."""
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError(_("Invalid email address."))
        return value


class EmailVerificationConfirmSerializer(serializers.Serializer):
    """Serializer for email verification confirmation."""

    token = serializers.CharField()


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_name', 'action', 'description', 'category',
            'ip_address', 'user_agent', 'metadata', 'organization',
            'organization_name', 'workspace', 'workspace_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserPreferencesSerializer(serializers.Serializer):
    """Serializer for user preferences."""

    timezone = serializers.CharField(max_length=50, required=False)
    language = serializers.CharField(max_length=10, required=False)
    work_hours_start = serializers.TimeField(required=False)
    work_hours_end = serializers.TimeField(required=False)
    work_days = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    email_notifications = serializers.BooleanField(required=False)
    push_notifications = serializers.BooleanField(required=False)
    weekly_digest = serializers.BooleanField(required=False)
    profile_visibility = serializers.ChoiceField(
        choices=['public', 'organization', 'team', 'private'],
        required=False
    )
    show_online_status = serializers.BooleanField(required=False)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    current_password = serializers.CharField(
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _("Current password is incorrect.")
            )
        return value

    def validate(self, data):
        """Validate new passwords match."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                _("New passwords do not match.")
            )
        return data


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics."""

    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    total_activities = serializers.IntegerField()
    recent_activities = serializers.ListField()
    login_streak = serializers.IntegerField()
    average_session_duration = serializers.IntegerField()
    most_active_day = serializers.CharField()
    most_active_hour = serializers.IntegerField()
    organizations_joined = serializers.IntegerField()
    workspaces_joined = serializers.IntegerField()
    teams_joined = serializers.IntegerField()
    tasks_created = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    time_entries_created = serializers.IntegerField()
    total_hours_tracked = serializers.DecimalField(max_digits=10, decimal_places=2)


class UserSearchSerializer(serializers.Serializer):
    """Serializer for user search."""

    query = serializers.CharField(max_length=100)
    organization_id = serializers.UUIDField(required=False)
    workspace_id = serializers.UUIDField(required=False)
    team_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)


class UserBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk user actions."""

    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of user IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'verify', 'unverify'],
        help_text=_('Action to perform on the users')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')
        user_ids = data.get('user_ids', [])

        if not user_ids:
            raise serializers.ValidationError(
                _("At least one user ID is required.")
            )

        return data


class UserExportSerializer(serializers.Serializer):
    """Serializer for exporting user data."""

    include_profile = serializers.BooleanField(default=True)
    include_sessions = serializers.BooleanField(default=False)
    include_activities = serializers.BooleanField(default=False)
    include_organizations = serializers.BooleanField(default=True)
    include_workspaces = serializers.BooleanField(default=True)
    include_teams = serializers.BooleanField(default=True)
    include_tasks = serializers.BooleanField(default=False)
    include_time_entries = serializers.BooleanField(default=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    format = serializers.ChoiceField(
        choices=['json', 'csv'],
        default='json'
    )


class UserImportSerializer(serializers.Serializer):
    """Serializer for importing user data."""

    file = serializers.FileField()
    import_mode = serializers.ChoiceField(
        choices=['create', 'update', 'merge'],
        default='create'
    )
    send_invitation = serializers.BooleanField(default=True)
    organization_id = serializers.UUIDField(required=False)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'}
    )
    remember_me = serializers.BooleanField(default=False)


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh."""

    refresh_token = serializers.CharField()


class MagicLinkRequestSerializer(serializers.Serializer):
    """Serializer for magic link requests."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("No active user found with this email address.")
            )
        return value


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for two-factor setup."""

    password = serializers.CharField(
        style={'input_type': 'password'}
    )


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for two-factor verification."""

    token = serializers.CharField(min_length=6, max_length=6)
    remember_device = serializers.BooleanField(default=False)


class PasskeyRegisterSerializer(serializers.Serializer):
    """Serializer for passkey registration."""

    name = serializers.CharField(max_length=100)


class PasskeyAuthenticateSerializer(serializers.Serializer):
    """Serializer for passkey authentication."""

    credential_id = serializers.CharField()
    authenticator_data = serializers.CharField()
    client_data_json = serializers.CharField()
    signature = serializers.CharField()


class UserNotificationSerializer(serializers.Serializer):
    """Serializer for user notifications."""

    id = serializers.UUIDField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    data = serializers.DictField()
    read = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class UserSettingsSerializer(serializers.Serializer):
    """Serializer for user settings."""

    # Profile settings
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, required=False)
    language = serializers.CharField(max_length=10, required=False)

    # Work preferences
    work_hours_start = serializers.TimeField(required=False)
    work_hours_end = serializers.TimeField(required=False)
    work_days = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    # Notification settings
    email_notifications = serializers.BooleanField(required=False)
    push_notifications = serializers.BooleanField(required=False)
    weekly_digest = serializers.BooleanField(required=False)

    # Privacy settings
    profile_visibility = serializers.ChoiceField(
        choices=['public', 'organization', 'team', 'private'],
        required=False
    )
    show_online_status = serializers.BooleanField(required=False)


class UserOnboardingSerializer(serializers.Serializer):
    """Serializer for user onboarding."""

    step = serializers.IntegerField(min_value=1, max_value=10)
    completed_steps = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    data = serializers.DictField(required=False)


class UserFeedbackSerializer(serializers.Serializer):
    """Serializer for user feedback."""

    type = serializers.ChoiceField(
        choices=['bug', 'feature', 'improvement', 'general'],
        default='general'
    )
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    category = serializers.CharField(max_length=50, required=False)
    priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'urgent'],
        default='medium'
    )
    metadata = serializers.DictField(required=False)