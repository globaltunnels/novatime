"""
Serializers for time_entries app.

This module contains serializers for TimeEntry, Timer, TimeEntryApproval,
IdlePeriod, TimeEntryTemplate, TimeEntryCategory, TimeEntryTag,
TimeEntryComment, TimeEntryAttachment, and related models for API
serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, fields
from decimal import Decimal

from .models import (
    TimeEntry, Timer, TimeEntryApproval, IdlePeriod, TimeEntryTemplate,
    TimeEntryCategory, TimeEntryTag, TimeEntryComment, TimeEntryAttachment
)


class TimeEntryCategorySerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryCategory model."""

    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntryCategory
        fields = [
            'id', 'name', 'description', 'color', 'icon', 'usage_count',
            'organization', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']

    def get_usage_count(self, obj):
        """Get usage count."""
        return obj.usage_count


class TimeEntryTagSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryTag model."""

    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntryTag
        fields = [
            'id', 'name', 'description', 'color', 'usage_count',
            'organization', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']

    def get_usage_count(self, obj):
        """Get usage count."""
        return obj.usage_count


class TimeEntryAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryAttachment model."""

    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = TimeEntryAttachment
        fields = [
            'id', 'time_entry', 'uploaded_by', 'uploaded_by_name', 'file', 'file_url',
            'filename', 'file_size', 'content_type', 'created_at'
        ]
        read_only_fields = ['id', 'file_url', 'created_at']

    def get_file_url(self, obj):
        """Get file URL."""
        if obj.file:
            return obj.file.url
        return None


class TimeEntryCommentSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryComment model."""

    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    replies_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntryComment
        fields = [
            'id', 'time_entry', 'author', 'author_name', 'content', 'parent_comment',
            'replies_count', 'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'replies_count', 'replies', 'created_at', 'updated_at']

    def get_replies_count(self, obj):
        """Get replies count."""
        return obj.replies.count()

    def get_replies(self, obj):
        """Get replies."""
        if self.context.get('include_replies', False):
            replies = obj.get_replies()
            return TimeEntryCommentSerializer(replies, many=True, context=self.context).data
        return []


class TimeEntryTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryTemplate model."""

    class Meta:
        model = TimeEntryTemplate
        fields = [
            'id', 'name', 'description', 'template_data', 'is_public', 'is_system',
            'usage_count', 'organization', 'workspace', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class IdlePeriodSerializer(serializers.ModelSerializer):
    """Serializer for IdlePeriod model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    timer_description = serializers.CharField(
        source='timer.description',
        read_only=True
    )
    duration_minutes = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = IdlePeriod
        fields = [
            'id', 'user', 'user_name', 'timer', 'timer_description', 'start_time',
            'end_time', 'duration_seconds', 'duration_minutes', 'reason',
            'context_data', 'action_taken', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'duration_minutes', 'is_active', 'created_at']

    def get_duration_minutes(self, obj):
        """Get duration in minutes."""
        return obj.get_duration_minutes()

    def get_is_active(self, obj):
        """Check if active."""
        return obj.is_active()


class TimerSerializer(serializers.ModelSerializer):
    """Serializer for Timer model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.title',
        read_only=True
    )

    # Computed fields
    elapsed_time = serializers.SerializerMethodField()
    elapsed_seconds = serializers.SerializerMethodField()
    elapsed_minutes = serializers.SerializerMethodField()
    is_idle = serializers.SerializerMethodField()
    cost_amount = serializers.SerializerMethodField()

    class Meta:
        model = Timer
        fields = [
            'id', 'user', 'user_name', 'organization', 'workspace', 'project',
            'project_name', 'task', 'task_title', 'description', 'start_time',
            'end_time', 'paused_at', 'total_paused_seconds', 'status',
            'is_billable', 'hourly_rate', 'idle_threshold_minutes',
            'last_activity_at', 'location', 'ip_address', 'elapsed_time',
            'elapsed_seconds', 'elapsed_minutes', 'is_idle', 'cost_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'elapsed_time', 'elapsed_seconds', 'elapsed_minutes',
            'is_idle', 'cost_amount', 'created_at', 'updated_at'
        ]

    def get_elapsed_time(self, obj):
        """Get elapsed time formatted."""
        return obj.get_elapsed_time()

    def get_elapsed_seconds(self, obj):
        """Get elapsed time in seconds."""
        return obj.get_elapsed_seconds()

    def get_elapsed_minutes(self, obj):
        """Get elapsed time in minutes."""
        return obj.get_elapsed_minutes()

    def get_is_idle(self, obj):
        """Check if idle."""
        return obj.is_idle()

    def get_cost_amount(self, obj):
        """Get calculated cost."""
        if obj.hourly_rate and obj.get_elapsed_minutes():
            hours = Decimal(obj.get_elapsed_minutes()) / 60
            return (hours * obj.hourly_rate).quantize(Decimal('0.01'))
        return Decimal('0.00')


class TimerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timers."""

    class Meta:
        model = Timer
        fields = [
            'project', 'task', 'description', 'is_billable', 'hourly_rate',
            'idle_threshold_minutes', 'location'
        ]

    def create(self, validated_data):
        """Create timer."""
        validated_data['user'] = self.context['request'].user
        validated_data['organization'] = self.context['request'].user.organization
        validated_data['workspace'] = self.context['request'].user.workspace
        return super().create(validated_data)


class TimeEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimeEntry model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.title',
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
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name',
        read_only=True
    )

    # Computed fields
    duration_hours = serializers.SerializerMethodField()
    cost_amount = serializers.SerializerMethodField()
    can_user_edit = serializers.SerializerMethodField()
    can_user_approve = serializers.SerializerMethodField()

    # Related data
    comments = TimeEntryCommentSerializer(many=True, read_only=True)
    attachments = TimeEntryAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'user', 'user_name', 'organization', 'organization_name',
            'workspace', 'workspace_name', 'project', 'project_name', 'task',
            'task_title', 'start_time', 'end_time', 'duration_minutes',
            'duration_hours', 'description', 'entry_type', 'is_billable',
            'hourly_rate', 'cost_amount', 'location', 'ip_address', 'user_agent',
            'status', 'submitted_at', 'approved_at', 'approved_by',
            'approved_by_name', 'rejection_reason', 'tags', 'categories',
            'custom_fields', 'integration_data', 'can_user_edit',
            'can_user_approve', 'comments', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'duration_hours', 'cost_amount', 'can_user_edit',
            'can_user_approve', 'comments', 'attachments', 'created_at', 'updated_at'
        ]

    def get_duration_hours(self, obj):
        """Get duration in hours."""
        return obj.get_duration_hours()

    def get_cost_amount(self, obj):
        """Get calculated cost."""
        return obj.get_cost()

    def get_can_user_edit(self, obj):
        """Check if user can edit."""
        return obj.can_user_edit(self.context['request'].user)

    def get_can_user_approve(self, obj):
        """Check if user can approve."""
        return obj.can_user_approve(self.context['request'].user)


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating time entries."""

    class Meta:
        model = TimeEntry
        fields = [
            'organization', 'workspace', 'project', 'task', 'start_time',
            'end_time', 'description', 'entry_type', 'is_billable',
            'hourly_rate', 'location', 'tags', 'categories', 'custom_fields'
        ]

    def validate_organization(self, value):
        """Validate organization access."""
        user = self.context['request'].user
        if not user.organizations.filter(id=value.id).exists():
            raise serializers.ValidationError(
                _("You don't have access to this organization.")
            )
        return value

    def validate_workspace(self, value):
        """Validate workspace access."""
        user = self.context['request'].user
        if not value.memberships.filter(user=user, is_active=True).exists():
            raise serializers.ValidationError(
                _("You don't have access to this workspace.")
            )
        return value

    def validate_project(self, value):
        """Validate project access."""
        if value and not value.can_user_access(self.context['request'].user):
            raise serializers.ValidationError(
                _("You don't have access to this project.")
            )
        return value

    def create(self, validated_data):
        """Create time entry."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TimeEntryApprovalSerializer(serializers.ModelSerializer):
    """Serializer for TimeEntryApproval model."""

    approver_name = serializers.CharField(
        source='approver.get_full_name',
        read_only=True
    )
    requested_by_name = serializers.CharField(
        source='requested_by.get_full_name',
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

    # Time entries data
    time_entries_data = serializers.SerializerMethodField()
    time_entries_count = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntryApproval
        fields = [
            'id', 'organization', 'organization_name', 'workspace', 'workspace_name',
            'approver', 'approver_name', 'requested_by', 'requested_by_name',
            'time_entries', 'time_entries_data', 'time_entries_count',
            'approval_type', 'period_start', 'period_end', 'status',
            'approver_comments', 'requested_notes', 'requested_at',
            'responded_at', 'total_hours', 'billable_hours', 'total_entries',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'time_entries_data', 'time_entries_count', 'requested_at',
            'responded_at', 'total_hours', 'billable_hours', 'total_entries',
            'created_at', 'updated_at'
        ]

    def get_time_entries_data(self, obj):
        """Get time entries data."""
        time_entries = obj.time_entries.all()
        return TimeEntrySerializer(time_entries, many=True, context=self.context).data

    def get_time_entries_count(self, obj):
        """Get time entries count."""
        return obj.time_entries.count()


class TimeEntryApprovalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating time entry approvals."""

    class Meta:
        model = TimeEntryApproval
        fields = [
            'approver', 'time_entries', 'approval_type', 'period_start',
            'period_end', 'requested_notes'
        ]

    def validate_approver(self, value):
        """Validate approver access."""
        user = self.context['request'].user
        workspace = self.context.get('workspace')

        if workspace and not workspace.memberships.filter(
            user=value,
            role__in=['owner', 'admin'],
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                _("Selected user doesn't have approval permissions in this workspace.")
            )
        return value

    def create(self, validated_data):
        """Create approval."""
        validated_data['requested_by'] = self.context['request'].user
        validated_data['organization'] = self.context['request'].user.organization
        validated_data['workspace'] = self.context.get('workspace')
        return super().create(validated_data)


class TimeEntryBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk time entry actions."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=[
            'submit', 'approve', 'reject', 'update_status', 'update_tags',
            'update_categories', 'delete'
        ],
        help_text=_('Action to perform on the time entries')
    )

    status = serializers.ChoiceField(
        choices=['draft', 'submitted', 'approved', 'rejected', 'locked'],
        required=False,
        help_text=_('New status (for update_status action)')
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Tags to add/remove')
    )

    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Categories to add/remove')
    )

    rejection_reason = serializers.CharField(
        required=False,
        help_text=_('Rejection reason (for reject action)')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')

        if action == 'update_status' and 'status' not in data:
            raise serializers.ValidationError(
                _("Status is required for update_status action.")
            )

        if action == 'reject' and 'rejection_reason' not in data:
            raise serializers.ValidationError(
                _("Rejection reason is required for reject action.")
            )

        return data


class TimerActionSerializer(serializers.Serializer):
    """Serializer for timer actions."""

    action = serializers.ChoiceField(
        choices=['start', 'pause', 'resume', 'stop'],
        help_text=_('Action to perform on the timer')
    )

    description = serializers.CharField(
        required=False,
        help_text=_('Description for the timer')
    )

    project_id = serializers.UUIDField(
        required=False,
        help_text=_('Project ID for the timer')
    )

    task_id = serializers.UUIDField(
        required=False,
        help_text=_('Task ID for the timer')
    )


class TimeEntryReportSerializer(serializers.Serializer):
    """Serializer for time entry reports."""

    start_date = serializers.DateField(help_text=_('Report start date'))
    end_date = serializers.DateField(help_text=_('Report end date'))
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by user IDs')
    )
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by project IDs')
    )
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by task IDs')
    )
    organization_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by organization IDs')
    )
    workspace_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by workspace IDs')
    )
    entry_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Filter by entry types')
    )
    statuses = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Filter by statuses')
    )
    is_billable = serializers.BooleanField(
        required=False,
        help_text=_('Filter by billable status')
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Filter by tags')
    )
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Filter by categories')
    )
    group_by = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['user', 'project', 'task', 'date', 'week', 'month']
        ),
        required=False,
        help_text=_('Group results by these fields')
    )


class TimeEntryStatsSerializer(serializers.Serializer):
    """Serializer for time entry statistics."""

    total_entries = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_hours_per_entry = serializers.DecimalField(max_digits=6, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_cost_per_hour = serializers.DecimalField(max_digits=8, decimal_places=2)
    entries_by_type = serializers.DictField()
    entries_by_status = serializers.DictField()
    hours_by_project = serializers.DictField()
    hours_by_user = serializers.DictField()
    hours_by_date = serializers.DictField()
    top_tags = serializers.ListField()
    top_categories = serializers.ListField()
    productivity_trend = serializers.ListField()
    cost_trend = serializers.ListField()


class TimerStatsSerializer(serializers.Serializer):
    """Serializer for timer statistics."""

    total_timers = serializers.IntegerField()
    active_timers = serializers.IntegerField()
    paused_timers = serializers.IntegerField()
    stopped_timers = serializers.IntegerField()
    total_tracked_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_session_length = serializers.DecimalField(max_digits=6, decimal_places=2)
    most_productive_day = serializers.CharField()
    most_productive_hour = serializers.IntegerField()
    idle_time_total = serializers.DecimalField(max_digits=8, decimal_places=2)
    idle_time_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    timers_by_project = serializers.DictField()
    timers_by_user = serializers.DictField()
    productivity_by_day = serializers.DictField()
    productivity_by_hour = serializers.DictField()


class TimeEntryImportSerializer(serializers.Serializer):
    """Serializer for importing time entries."""

    file = serializers.FileField(help_text=_('CSV or Excel file to import'))
    organization_id = serializers.UUIDField(help_text=_('Organization ID'))
    workspace_id = serializers.UUIDField(help_text=_('Workspace ID'))
    date_format = serializers.CharField(
        default='%Y-%m-%d',
        help_text=_('Date format in the file')
    )
    time_format = serializers.CharField(
        default='%H:%M:%S',
        help_text=_('Time format in the file')
    )
    delimiter = serializers.CharField(
        default=',',
        help_text=_('CSV delimiter')
    )
    has_header = serializers.BooleanField(
        default=True,
        help_text=_('Whether the file has a header row')
    )
    mapping = serializers.DictField(
        help_text=_('Column mapping for import')
    )


class TimeEntryExportSerializer(serializers.Serializer):
    """Serializer for exporting time entries."""

    start_date = serializers.DateField(help_text=_('Export start date'))
    end_date = serializers.DateField(help_text=_('Export end date'))
    format = serializers.ChoiceField(
        choices=['csv', 'excel', 'json', 'pdf'],
        default='csv',
        help_text=_('Export format')
    )
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by user IDs')
    )
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Filter by project IDs')
    )
    include_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Fields to include in export')
    )
    group_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Group results by these fields')
    )


class TimerSettingsSerializer(serializers.Serializer):
    """Serializer for timer settings."""

    idle_threshold_minutes = serializers.IntegerField(
        min_value=1,
        max_value=480,
        default=5,
        help_text=_('Minutes of inactivity before timer pauses')
    )
    auto_start_on_login = serializers.BooleanField(
        default=False,
        help_text=_('Automatically start timer when user logs in')
    )
    auto_stop_on_logout = serializers.BooleanField(
        default=True,
        help_text=_('Automatically stop timer when user logs out')
    )
    default_project_id = serializers.UUIDField(
        required=False,
        help_text=_('Default project for new timers')
    )
    default_task_id = serializers.UUIDField(
        required=False,
        help_text=_('Default task for new timers')
    )
    default_hourly_rate = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        help_text=_('Default hourly rate for timers')
    )
    reminder_interval_minutes = serializers.IntegerField(
        min_value=5,
        max_value=480,
        default=60,
        help_text=_('Minutes between timer reminders')
    )
    enable_idle_detection = serializers.BooleanField(
        default=True,
        help_text=_('Enable idle time detection')
    )
    enable_location_tracking = serializers.BooleanField(
        default=False,
        help_text=_('Enable location tracking for timers')
    )
    enable_screenshots = serializers.BooleanField(
        default=False,
        help_text=_('Enable screenshot capture (privacy consideration)')
    )


class TimeEntryReminderSerializer(serializers.Serializer):
    """Serializer for time entry reminders."""

    reminder_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'custom'],
        help_text=_('Type of reminder')
    )
    reminder_time = serializers.TimeField(
        required=False,
        help_text=_('Time to send reminder')
    )
    reminder_days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        required=False,
        help_text=_('Days of week to send reminders (0=Monday)')
    )
    reminder_message = serializers.CharField(
        max_length=500,
        required=False,
        help_text=_('Custom reminder message')
    )
    is_active = serializers.BooleanField(
        default=True,
        help_text=_('Whether the reminder is active')
    )


class TimeEntryIntegrationSerializer(serializers.Serializer):
    """Serializer for time entry integrations."""

    integration_type = serializers.ChoiceField(
        choices=['jira', 'github', 'gitlab', 'trello', 'asana', 'slack', 'teams'],
        help_text=_('Type of integration')
    )
    integration_id = serializers.CharField(
        help_text=_('Integration identifier')
    )
    sync_direction = serializers.ChoiceField(
        choices=['import', 'export', 'bidirectional'],
        default='bidirectional',
        help_text=_('Direction of synchronization')
    )
    sync_fields = serializers.ListField(
        child=serializers.CharField(),
        help_text=_('Fields to synchronize')
    )
    sync_interval_minutes = serializers.IntegerField(
        min_value=5,
        max_value=1440,
        default=60,
        help_text=_('Synchronization interval in minutes')
    )
    last_sync_at = serializers.DateTimeField(
        read_only=True,
        help_text=_('Last synchronization time')
    )
    is_active = serializers.BooleanField(
        default=True,
        help_text=_('Whether the integration is active')
    )


class TimeEntryTemplateApplySerializer(serializers.Serializer):
    """Serializer for applying time entry templates."""

    template_id = serializers.UUIDField(help_text=_('Template ID to apply'))
    start_time = serializers.DateTimeField(help_text=_('Start time for the time entry'))
    duration_minutes = serializers.IntegerField(
        min_value=1,
        help_text=_('Duration in minutes')
    )
    overrides = serializers.DictField(
        required=False,
        help_text=_('Field overrides for the template')
    )


class TimeEntryDuplicateSerializer(serializers.Serializer):
    """Serializer for duplicating time entries."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to duplicate')
    )
    date_offset_days = serializers.IntegerField(
        default=0,
        help_text=_('Number of days to offset the duplicated entries')
    )
    user_id = serializers.UUIDField(
        required=False,
        help_text=_('User ID for the duplicated entries (optional)')
    )
    project_id = serializers.UUIDField(
        required=False,
        help_text=_('Project ID for the duplicated entries (optional)')
    )
    task_id = serializers.UUIDField(
        required=False,
        help_text=_('Task ID for the duplicated entries (optional)')
    )


class TimeEntryMergeSerializer(serializers.Serializer):
    """Serializer for merging time entries."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to merge')
    )
    primary_entry_id = serializers.UUIDField(
        help_text=_('ID of the primary time entry to keep')
    )
    merge_description = serializers.BooleanField(
        default=True,
        help_text=_('Whether to merge descriptions')
    )
    merge_tags = serializers.BooleanField(
        default=True,
        help_text=_('Whether to merge tags')
    )
    merge_attachments = serializers.BooleanField(
        default=True,
        help_text=_('Whether to merge attachments')
    )


class TimeEntrySplitSerializer(serializers.Serializer):
    """Serializer for splitting time entries."""

    time_entry_id = serializers.UUIDField(help_text=_('ID of the time entry to split'))
    split_points = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        help_text=_('Duration in minutes for each split part')
    )
    descriptions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Descriptions for each split part')
    )


class TimeEntryLockSerializer(serializers.Serializer):
    """Serializer for locking time entries."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to lock')
    )
    lock_reason = serializers.CharField(
        required=False,
        help_text=_('Reason for locking the entries')
    )


class TimeEntryUnlockSerializer(serializers.Serializer):
    """Serializer for unlocking time entries."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of time entry IDs to unlock')
    )
    unlock_reason = serializers.CharField(
        required=False,
        help_text=_('Reason for unlocking the entries')
    )


class TimeEntryAuditSerializer(serializers.Serializer):
    """Serializer for time entry audit trail."""

    time_entry_id = serializers.UUIDField(help_text=_('Time entry ID'))
    include_system_changes = serializers.BooleanField(
        default=True,
        help_text=_('Include system-generated changes')
    )
    include_user_changes = serializers.BooleanField(
        default=True,
        help_text=_('Include user-generated changes')
    )
    start_date = serializers.DateField(
        required=False,
        help_text=_('Start date for audit trail')
    )
    end_date = serializers.DateField(
        required=False,
        help_text=_('End date for audit trail')
    )


class TimeEntryAuditEntrySerializer(serializers.Serializer):
    """Serializer for individual audit entries."""

    timestamp = serializers.DateTimeField()
    user = serializers.CharField()
    action = serializers.CharField()
    field = serializers.CharField()
    old_value = serializers.CharField()
    new_value = serializers.CharField()
    ip_address = serializers.IPAddressField()
    user_agent = serializers.CharField()


class TimeEntryForecastSerializer(serializers.Serializer):
    """Serializer for time entry forecasting."""

    user_id = serializers.UUIDField(required=False, help_text=_('User ID for forecasting'))
    project_id = serializers.UUIDField(required=False, help_text=_('Project ID for forecasting'))
    task_id = serializers.UUIDField(required=False, help_text=_('Task ID for forecasting'))
    forecast_days = serializers.IntegerField(
        min_value=1,
        max_value=365,
        default=30,
        help_text=_('Number of days to forecast')
    )
    include_holidays = serializers.BooleanField(
        default=True,
        help_text=_('Include holidays in forecast')
    )
    include_vacation = serializers.BooleanField(
        default=True,
        help_text=_('Include vacation time in forecast')
    )


class TimeEntryForecastResultSerializer(serializers.Serializer):
    """Serializer for forecast results."""

    forecast_date = serializers.DateField()
    predicted_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    confidence_level = serializers.DecimalField(max_digits=5, decimal_places=2)
    factors = serializers.ListField()
    recommendations = serializers.ListField()


class TimeEntryProductivitySerializer(serializers.Serializer):
    """Serializer for productivity analysis."""

    user_id = serializers.UUIDField(required=False, help_text=_('User ID for analysis'))
    start_date = serializers.DateField(help_text=_('Analysis start date'))
    end_date = serializers.DateField(help_text=_('Analysis end date'))
    include_idle_time = serializers.BooleanField(
        default=True,
        help_text=_('Include idle time in analysis')
    )
    include_break_time = serializers.BooleanField(
        default=True,
        help_text=_('Include break time in analysis')
    )


class TimeEntryProductivityResultSerializer(serializers.Serializer):
    """Serializer for productivity results."""

    total_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    productive_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    idle_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    break_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    productivity_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    efficiency_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    focus_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    recommendations = serializers.ListField()
    trends = serializers.ListField()
    insights = serializers.ListField()


class TimeEntryComplianceSerializer(serializers.Serializer):
    """Serializer for compliance checking."""

    time_entry_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('Specific time entries to check')
    )
    organization_id = serializers.UUIDField(
        required=False,
        help_text=_('Organization ID for compliance check')
    )
    workspace_id = serializers.UUIDField(
        required=False,
        help_text=_('Workspace ID for compliance check')
    )
    start_date = serializers.DateField(
        required=False,
        help_text=_('Start date for compliance check')
    )
    end_date = serializers.DateField(
        required=False,
        help_text=_('End date for compliance check')
    )
    check_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['overtime', 'breaks', 'location', 'approval', 'tampering']
        ),
        help_text=_('Types of compliance checks to perform')
    )


class TimeEntryComplianceResultSerializer(serializers.Serializer):
    """Serializer for compliance results."""

    check_type = serializers.CharField()
    status = serializers.CharField()
    violations = serializers.ListField()
    recommendations = serializers.ListField()
    severity = serializers.CharField()
    compliance_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class TimeEntryBackupSerializer(serializers.Serializer):
    """Serializer for time entry backups."""

    organization_id = serializers.UUIDField(help_text=_('Organization ID to backup'))
    workspace_id = serializers.UUIDField(
        required=False,
        help_text=_('Workspace ID to backup (optional)')
    )
    start_date = serializers.DateField(
        required=False,
        help_text=_('Start date for backup')
    )
    end_date = serializers.DateField(
        required=False,
        help_text=_('End date for backup')
    )
    include_attachments = serializers.BooleanField(
        default=True,
        help_text=_('Include attachments in backup')
    )
    include_comments = serializers.BooleanField(
        default=True,
        help_text=_('Include comments in backup')
    )
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel', 'sql'],
        default='json',
        help_text=_('Backup format')
    )


class TimeEntryRestoreSerializer(serializers.Serializer):
    """Serializer for time entry restoration."""

    backup_file = serializers.FileField(help_text=_('Backup file to restore'))
    organization_id = serializers.UUIDField(help_text=_('Organization ID to restore to'))
    workspace_id = serializers.UUIDField(
        required=False,
        help_text=_('Workspace ID to restore to')
    )
    restore_mode = serializers.ChoiceField(
        choices=['merge', 'replace', 'append'],
        default='merge',
        help_text=_('How to handle conflicts during restore')
    )
    preview_only = serializers.BooleanField(
        default=False,
        help_text=_('Only preview the restore without actually doing it')
    )