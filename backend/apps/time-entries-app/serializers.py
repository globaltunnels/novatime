"""
Serializers for time entries app.

This module contains serializers for TimeEntry, Timer, IdlePeriod,
and related models for API serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import (
    TimeEntry, Timer, IdlePeriod, TimeEntryTemplate, TimeEntryComment
)


class TimeEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimeEntry model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.title',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name',
        read_only=True
    )

    duration_display = serializers.SerializerMethodField()
    cost_display = serializers.SerializerMethodField()
    is_running = serializers.SerializerMethodField()
    overlap_entries_count = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'user', 'user_name', 'workspace', 'workspace_name',
            'task', 'task_title', 'project', 'project_name', 'start_time',
            'end_time', 'duration_minutes', 'duration_display', 'description',
            'is_billable', 'hourly_rate', 'cost_amount', 'cost_display',
            'location', 'ip_address', 'user_agent', 'device_type',
            'operating_system', 'productivity_score', 'focus_score',
            'idle_minutes', 'tags', 'custom_fields', 'ai_generated',
            'ai_confidence', 'is_approved', 'approved_by', 'approved_by_name',
            'approved_at', 'approval_notes', 'is_active', 'created_at',
            'updated_at', 'is_running', 'overlap_entries_count'
        ]
        read_only_fields = [
            'id', 'duration_minutes', 'cost_amount', 'created_at', 'updated_at'
        ]

    def get_duration_display(self, obj):
        """Get human-readable duration."""
        return obj.get_duration_display()

    def get_cost_display(self, obj):
        """Get formatted cost display."""
        return obj.get_cost_display()

    def get_is_running(self, obj):
        """Check if entry is running."""
        return obj.is_running()

    def get_overlap_entries_count(self, obj):
        """Get count of overlapping entries."""
        return obj.get_overlap_entries().count()


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating time entries."""

    class Meta:
        model = TimeEntry
        fields = [
            'task', 'project', 'start_time', 'end_time', 'description',
            'is_billable', 'hourly_rate', 'location', 'tags', 'custom_fields'
        ]

    def validate(self, data):
        """Validate time entry data."""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        task = data.get('task')
        project = data.get('project')

        # Validate times
        if end_time and end_time <= start_time:
            raise serializers.ValidationError(
                _("End time must be after start time.")
            )

        # Validate task/project association
        if task and project and task.project != project:
            raise serializers.ValidationError(
                _("Task must belong to the specified project.")
            )

        # Set project from task if not specified
        if task and not project:
            data['project'] = task.project

        return data

    def create(self, validated_data):
        """Create time entry with current user and workspace."""
        validated_data['user'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimerSerializer(serializers.ModelSerializer):
    """Serializer for Timer model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.title',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )

    current_duration_minutes = serializers.SerializerMethodField()
    current_duration_display = serializers.SerializerMethodField()
    is_idle = serializers.SerializerMethodField()

    class Meta:
        model = Timer
        fields = [
            'id', 'user', 'user_name', 'workspace', 'workspace_name',
            'task', 'task_title', 'project', 'project_name', 'description',
            'start_time', 'paused_at', 'total_paused_minutes', 'status',
            'is_billable', 'hourly_rate', 'idle_threshold_minutes',
            'auto_stop_on_idle', 'track_location', 'is_active', 'created_at',
            'updated_at', 'current_duration_minutes', 'current_duration_display',
            'is_idle'
        ]
        read_only_fields = [
            'id', 'paused_at', 'total_paused_minutes', 'created_at', 'updated_at'
        ]

    def get_current_duration_minutes(self, obj):
        """Get current duration in minutes."""
        return obj.get_current_duration_minutes()

    def get_current_duration_display(self, obj):
        """Get human-readable current duration."""
        return obj.get_current_duration_display()

    def get_is_idle(self, obj):
        """Check if timer is idle."""
        return obj.is_idle()


class TimerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timers."""

    class Meta:
        model = Timer
        fields = [
            'task', 'project', 'description', 'is_billable', 'hourly_rate',
            'idle_threshold_minutes', 'auto_stop_on_idle', 'track_location'
        ]

    def validate(self, data):
        """Validate timer data."""
        user = self.context['request'].user
        task = data.get('task')
        project = data.get('project')

        # Check for existing running timer
        running_timer = Timer.objects.filter(
            user=user,
            status='running',
            is_active=True
        ).first()

        if running_timer:
            raise serializers.ValidationError(
                _("You already have a running timer. Please stop it first.")
            )

        # Validate task/project association
        if task and project and task.project != project:
            raise serializers.ValidationError(
                _("Task must belong to the specified project.")
            )

        # Set project from task if not specified
        if task and not project:
            data['project'] = task.project

        return data

    def create(self, validated_data):
        """Create timer with current user and workspace."""
        validated_data['user'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        validated_data['start_time'] = timezone.now()
        return super().create(validated_data)


class IdlePeriodSerializer(serializers.ModelSerializer):
    """Serializer for IdlePeriod model."""

    class Meta:
        model = IdlePeriod
        fields = [
            'id', 'time_entry', 'start_time', 'end_time', 'duration_minutes',
            'detection_method', 'active_application', 'active_window_title',
            'created_at'
        ]
        read_only_fields = [
            'id', 'duration_minutes', 'created_at'
        ]


class TimeEntryTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryTemplate model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )

    class Meta:
        model = TimeEntryTemplate
        fields = [
            'id', 'user', 'user_name', 'workspace', 'workspace_name', 'name',
            'description', 'template_data', 'is_recurring', 'recurrence_pattern',
            'recurrence_interval', 'default_duration_minutes', 'default_is_billable',
            'default_hourly_rate', 'usage_count', 'is_active', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'usage_count', 'created_at', 'updated_at', 'user'
        ]


class TimeEntryTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating time entry templates."""

    class Meta:
        model = TimeEntryTemplate
        fields = [
            'name', 'description', 'template_data', 'is_recurring',
            'recurrence_pattern', 'recurrence_interval', 'default_duration_minutes',
            'default_is_billable', 'default_hourly_rate', 'is_public'
        ]

    def create(self, validated_data):
        """Create template with current user."""
        validated_data['user'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimeEntryCommentSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryComment model."""

    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    author_avatar = serializers.ImageField(
        source='author.profile.avatar',
        read_only=True
    )

    class Meta:
        model = TimeEntryComment
        fields = [
            'id', 'time_entry', 'author', 'author_name', 'author_avatar',
            'content', 'comment_type', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        """Create comment with current user as author."""
        validated_data['author'] = self.context['request'].user
        validated_data['time_entry'] = self.context['time_entry']
        return super().create(validated_data)


class TimerActionSerializer(serializers.Serializer):
    """Serializer for timer actions."""

    action = serializers.ChoiceField(
        choices=['start', 'pause', 'resume', 'stop'],
        help_text=_('Action to perform on the timer')
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Timer description (for start action)')
    )

    task = serializers.UUIDField(
        required=False,
        help_text=_('Task ID to associate (for start action)')
    )

    project = serializers.UUIDField(
        required=False,
        help_text=_('Project ID to associate (for start action)')
    )


class TimeEntryBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk time entry actions."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'delete', 'update_tags'],
        help_text=_('Action to perform on the time entries')
    )

    approval_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Approval notes (for approve/reject actions)')
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Tags to add/update (for update_tags action)')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')

        if action in ['approve', 'reject'] and 'approval_notes' not in data:
            data['approval_notes'] = ''

        if action == 'update_tags' and 'tags' not in data:
            raise serializers.ValidationError(
                _("Tags are required for update_tags action.")
            )

        return data


class TimeEntryReportSerializer(serializers.Serializer):
    """Serializer for time entry reporting parameters."""

    workspace = serializers.UUIDField(
        required=False,
        help_text=_('Workspace ID to filter by')
    )

    user = serializers.UUIDField(
        required=False,
        help_text=_('User ID to filter by')
    )

    task = serializers.UUIDField(
        required=False,
        help_text=_('Task ID to filter by')
    )

    project = serializers.UUIDField(
        required=False,
        help_text=_('Project ID to filter by')
    )

    start_date = serializers.DateField(
        required=False,
        help_text=_('Start date for the report')
    )

    end_date = serializers.DateField(
        required=False,
        help_text=_('End date for the report')
    )

    is_billable = serializers.BooleanField(
        required=False,
        help_text=_('Filter by billable status')
    )

    is_approved = serializers.BooleanField(
        required=False,
        help_text=_('Filter by approval status')
    )

    group_by = serializers.ChoiceField(
        choices=['user', 'task', 'project', 'date', 'week', 'month'],
        required=False,
        default='user',
        help_text=_('How to group the results')
    )

    include_idle_time = serializers.BooleanField(
        required=False,
        default=False,
        help_text=_('Whether to include idle time in calculations')
    )


class TimeTrackingStatsSerializer(serializers.Serializer):
    """Serializer for time tracking statistics."""

    total_entries = serializers.IntegerField()
    total_minutes = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_minutes = serializers.IntegerField()
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_productivity_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_focus_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_idle_minutes = serializers.IntegerField()
    most_productive_day = serializers.DateField()
    longest_session_minutes = serializers.IntegerField()
    average_session_minutes = serializers.DecimalField(max_digits=8, decimal_places=2)


class TimerStatsSerializer(serializers.Serializer):
    """Serializer for timer statistics."""

    total_timers_started = serializers.IntegerField()
    total_time_tracked_minutes = serializers.IntegerField()
    average_session_minutes = serializers.DecimalField(max_digits=8, decimal_places=2)
    most_used_task = serializers.CharField()
    most_used_project = serializers.CharField()
    total_idle_time_minutes = serializers.IntegerField()
    auto_stop_events = serializers.IntegerField()
    manual_stop_events = serializers.IntegerField()


class TimeEntryApprovalSerializer(serializers.Serializer):
    """Serializer for time entry approval."""

    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        help_text=_('Approval action')
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Approval notes')
    )


class TimeEntryFromTemplateSerializer(serializers.Serializer):
    """Serializer for creating time entry from template."""

    template = serializers.UUIDField(
        help_text=_('Template ID to use')
    )

    start_time = serializers.DateTimeField(
        required=False,
        help_text=_('Start time (defaults to now)')
    )

    duration_minutes = serializers.IntegerField(
        required=False,
        help_text=_('Duration in minutes (overrides template default)')
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Description (overrides template)')
    )

    task = serializers.UUIDField(
        required=False,
        help_text=_('Task ID (overrides template)')
    )

    project = serializers.UUIDField(
        required=False,
        help_text=_('Project ID (overrides template)')
    )