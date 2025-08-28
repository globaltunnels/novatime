"""
Serializers for timesheets app.

This module contains serializers for Timesheet, TimesheetPeriod,
TimesheetEntry, and related models for API serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import (
    Timesheet, TimesheetPeriod, TimesheetEntry, ApprovalWorkflow,
    TimesheetComment, TimesheetTemplate
)


class TimesheetPeriodSerializer(serializers.ModelSerializer):
    """Serializer for TimesheetPeriod model."""

    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    is_submission_open = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    total_users = serializers.SerializerMethodField()
    submitted_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = TimesheetPeriod
        fields = [
            'id', 'workspace', 'workspace_name', 'name', 'period_type',
            'start_date', 'end_date', 'is_active', 'auto_create_timesheets',
            'submission_deadline_days', 'require_approval', 'auto_approve_after_days',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_submission_open', 'is_overdue', 'total_users', 'submitted_count',
            'completion_percentage'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_is_submission_open(self, obj):
        """Check if submission is open."""
        return obj.is_submission_open()

    def get_is_overdue(self, obj):
        """Check if period is overdue."""
        return obj.is_overdue()

    def get_total_users(self, obj):
        """Get total users count."""
        return obj.get_total_users()

    def get_submitted_count(self, obj):
        """Get submitted count."""
        return obj.get_submitted_count()

    def get_completion_percentage(self, obj):
        """Get completion percentage."""
        return obj.get_completion_percentage()


class TimesheetPeriodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timesheet periods."""

    class Meta:
        model = TimesheetPeriod
        fields = [
            'name', 'period_type', 'start_date', 'end_date',
            'auto_create_timesheets', 'submission_deadline_days',
            'require_approval', 'auto_approve_after_days'
        ]

    def validate(self, data):
        """Validate period data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if end_date <= start_date:
            raise serializers.ValidationError(
                _("End date must be after start date.")
            )

        # Check for overlapping periods in the same workspace
        workspace = self.context['request'].user.organizations.first().workspaces.first()
        if workspace:
            overlapping = TimesheetPeriod.objects.filter(
                workspace=workspace,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exclude(pk=self.instance.pk if self.instance else None)

            if overlapping.exists():
                raise serializers.ValidationError(
                    _("This period overlaps with an existing period.")
                )

        return data

    def create(self, validated_data):
        """Create period with current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimesheetSerializer(serializers.ModelSerializer):
    """Serializer for Timesheet model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    period_name = serializers.CharField(
        source='period.name',
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name',
        read_only=True
    )
    completion_percentage = serializers.SerializerMethodField()
    quality_issues = serializers.SerializerMethodField()
    entries_count = serializers.SerializerMethodField()

    class Meta:
        model = Timesheet
        fields = [
            'id', 'user', 'user_name', 'workspace', 'workspace_name',
            'period', 'period_name', 'title', 'status', 'total_hours',
            'billable_hours', 'total_cost', 'submitted_at', 'approved_at',
            'approved_by', 'approved_by_name', 'rejection_reason',
            'approval_workflow', 'quality_score', 'quality_issues',
            'ai_generated', 'ai_suggestions', 'custom_fields', 'is_active',
            'created_at', 'updated_at', 'completion_percentage', 'entries_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_completion_percentage(self, obj):
        """Get completion percentage."""
        return obj.get_completion_percentage()

    def get_quality_issues(self, obj):
        """Get quality issues."""
        return obj.get_quality_issues()

    def get_entries_count(self, obj):
        """Get entries count."""
        return obj.entries.count()


class TimesheetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timesheets."""

    class Meta:
        model = Timesheet
        fields = [
            'period', 'title'
        ]

    def validate(self, data):
        """Validate timesheet data."""
        period = data.get('period')
        user = self.context['request'].user

        # Check if user already has a timesheet for this period
        existing = Timesheet.objects.filter(
            user=user,
            period=period
        ).first()

        if existing:
            raise serializers.ValidationError(
                _("You already have a timesheet for this period.")
            )

        return data

    def create(self, validated_data):
        """Create timesheet with current user."""
        validated_data['user'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimesheetEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimesheetEntry model."""

    time_entry_details = serializers.SerializerMethodField()
    effective_hours = serializers.SerializerMethodField()
    effective_rate = serializers.SerializerMethodField()

    class Meta:
        model = TimesheetEntry
        fields = [
            'id', 'timesheet', 'time_entry', 'time_entry_details',
            'notes', 'adjusted_hours', 'adjusted_rate', 'effective_hours',
            'effective_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_time_entry_details(self, obj):
        """Get time entry details."""
        from time_entries.serializers import TimeEntrySerializer
        return TimeEntrySerializer(obj.time_entry).data

    def get_effective_hours(self, obj):
        """Get effective hours."""
        return obj.get_effective_hours()

    def get_effective_rate(self, obj):
        """Get effective rate."""
        return obj.get_effective_rate()


class TimesheetEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding entries to timesheets."""

    class Meta:
        model = TimesheetEntry
        fields = [
            'time_entry', 'notes', 'adjusted_hours', 'adjusted_rate'
        ]

    def validate(self, data):
        """Validate entry data."""
        timesheet = self.context['timesheet']
        time_entry = data.get('time_entry')

        # Check if entry is already in the timesheet
        existing = TimesheetEntry.objects.filter(
            timesheet=timesheet,
            time_entry=time_entry
        ).first()

        if existing:
            raise serializers.ValidationError(
                _("This time entry is already in the timesheet.")
            )

        # Check if entry belongs to the same user and period
        if time_entry.user != timesheet.user:
            raise serializers.ValidationError(
                _("Time entry must belong to the same user as the timesheet.")
            )

        if not (timesheet.period.start_date <= time_entry.start_time.date() <= timesheet.period.end_date):
            raise serializers.ValidationError(
                _("Time entry must be within the timesheet period.")
            )

        return data

    def create(self, validated_data):
        """Create timesheet entry."""
        validated_data['timesheet'] = self.context['timesheet']
        return super().create(validated_data)


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for ApprovalWorkflow model."""

    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id', 'workspace', 'workspace_name', 'name', 'description',
            'workflow_type', 'steps', 'conditions', 'auto_approve_rules',
            'is_active', 'is_default', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ApprovalWorkflowCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating approval workflows."""

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'name', 'description', 'workflow_type', 'steps',
            'conditions', 'auto_approve_rules', 'is_default'
        ]

    def create(self, validated_data):
        """Create workflow with current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimesheetCommentSerializer(serializers.ModelSerializer):
    """Serializer for TimesheetComment model."""

    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    author_avatar = serializers.ImageField(
        source='author.profile.avatar',
        read_only=True
    )

    class Meta:
        model = TimesheetComment
        fields = [
            'id', 'timesheet', 'author', 'author_name', 'author_avatar',
            'content', 'comment_type', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimesheetCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timesheet comments."""

    class Meta:
        model = TimesheetComment
        fields = ['content', 'comment_type', 'is_private']

    def create(self, validated_data):
        """Create comment with current user as author."""
        validated_data['author'] = self.context['request'].user
        validated_data['timesheet'] = self.context['timesheet']
        return super().create(validated_data)


class TimesheetTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TimesheetTemplate model."""

    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = TimesheetTemplate
        fields = [
            'id', 'workspace', 'workspace_name', 'name', 'description',
            'template_data', 'auto_include_entries', 'include_rules',
            'usage_count', 'is_active', 'is_public', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at', 'created_by']


class TimesheetTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating timesheet templates."""

    class Meta:
        model = TimesheetTemplate
        fields = [
            'name', 'description', 'template_data', 'auto_include_entries',
            'include_rules', 'is_public'
        ]

    def create(self, validated_data):
        """Create template with current user."""
        validated_data['created_by'] = self.context['request'].user
        validated_data['workspace'] = self.context['request'].user.organizations.first().workspaces.first()
        return super().create(validated_data)


class TimesheetBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk timesheet actions."""

    timesheet_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of timesheet IDs to act upon')
    )
    action = serializers.ChoiceField(
        choices=['submit', 'approve', 'reject'],
        help_text=_('Action to perform on the timesheets')
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Reason for rejection (required for reject action)')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')
        reason = data.get('reason', '')

        if action == 'reject' and not reason.strip():
            raise serializers.ValidationError(
                _("Reason is required for rejection.")
            )

        return data


class TimesheetReportSerializer(serializers.Serializer):
    """Serializer for timesheet reporting parameters."""

    workspace = serializers.UUIDField(
        required=False,
        help_text=_('Workspace ID to filter by')
    )
    period = serializers.UUIDField(
        required=False,
        help_text=_('Timesheet period ID to filter by')
    )
    user = serializers.UUIDField(
        required=False,
        help_text=_('User ID to filter by')
    )
    status = serializers.ChoiceField(
        choices=['draft', 'submitted', 'approved', 'rejected', 'auto_approved'],
        required=False,
        help_text=_('Status to filter by')
    )
    start_date = serializers.DateField(
        required=False,
        help_text=_('Start date for the report')
    )
    end_date = serializers.DateField(
        required=False,
        help_text=_('End date for the report')
    )
    group_by = serializers.ChoiceField(
        choices=['user', 'period', 'status', 'workspace'],
        required=False,
        default='user',
        help_text=_('How to group the results')
    )


class TimesheetSummarySerializer(serializers.Serializer):
    """Serializer for timesheet summary data."""

    total_timesheets = serializers.IntegerField()
    submitted_timesheets = serializers.IntegerField()
    approved_timesheets = serializers.IntegerField()
    rejected_timesheets = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_quality_score = serializers.FloatField()
    on_time_submission_rate = serializers.FloatField()
    approval_time_avg = serializers.FloatField()
    timesheets_by_status = serializers.DictField()
    timesheets_by_period = serializers.DictField()
    top_submitters = serializers.ListField()
    quality_issues_summary = serializers.DictField()


class TimesheetTransitionSerializer(serializers.Serializer):
    """Serializer for timesheet status transitions."""

    status = serializers.ChoiceField(
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        help_text=_('New status for the timesheet')
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Optional comment for the status change')
    )

    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Reason for rejection (required if status is rejected)')
    )

    def validate(self, data):
        """Validate transition data."""
        status = data.get('status')
        rejection_reason = data.get('rejection_reason', '')

        if status == 'rejected' and not rejection_reason.strip():
            raise serializers.ValidationError(
                _("Rejection reason is required when rejecting a timesheet.")
            )

        return data