"""
Timesheets models for NovaTime.

This app handles timesheet management, approvals, periods,
and all timesheet-related functionality including workflows.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class TimesheetPeriod(models.Model):
    """
    Timesheet period model for defining reporting periods.

    Defines the time periods for which timesheets are submitted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheet_periods',
        help_text=_('Workspace this period belongs to')
    )

    name = models.CharField(
        _('period name'),
        max_length=100,
        help_text=_('Display name for the period')
    )

    period_type = models.CharField(
        _('period type'),
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('custom', 'Custom'),
        ],
        default='weekly',
        help_text=_('Type of timesheet period')
    )

    start_date = models.DateField(
        _('start date'),
        help_text=_('Start date of the period')
    )

    end_date = models.DateField(
        _('end date'),
        help_text=_('End date of the period')
    )

    # Period settings
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this period is active for submissions')
    )

    auto_create_timesheets = models.BooleanField(
        _('auto-create timesheets'),
        default=True,
        help_text=_('Whether to automatically create timesheets for users')
    )

    submission_deadline_days = models.PositiveIntegerField(
        _('submission deadline days'),
        default=1,
        help_text=_('Days after period end when submissions are due')
    )

    # Approval settings
    require_approval = models.BooleanField(
        _('require approval'),
        default=True,
        help_text=_('Whether timesheets require approval')
    )

    auto_approve_after_days = models.PositiveIntegerField(
        _('auto-approve after days'),
        null=True,
        blank=True,
        help_text=_('Automatically approve after this many days')
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_timesheet_periods',
        help_text=_('User who created this period')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workspace', '-start_date']
        verbose_name = _('timesheet period')
        verbose_name_plural = _('timesheet periods')
        unique_together = ['workspace', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.workspace.name}: {self.name} ({self.start_date} - {self.end_date})"

    def is_submission_open(self):
        """Check if submission is still open for this period."""
        from django.utils import timezone
        from datetime import timedelta

        deadline = self.end_date + timedelta(days=self.submission_deadline_days)
        return timezone.now().date() <= deadline

    def is_overdue(self):
        """Check if the period is overdue for submission."""
        from django.utils import timezone
        from datetime import timedelta

        deadline = self.end_date + timedelta(days=self.submission_deadline_days)
        return timezone.now().date() > deadline

    def get_total_users(self):
        """Get total number of users in the workspace."""
        return self.workspace.memberships.filter(is_active=True).count()

    def get_submitted_count(self):
        """Get number of submitted timesheets for this period."""
        return self.timesheets.filter(status='submitted').count()

    def get_completion_percentage(self):
        """Get completion percentage for this period."""
        total_users = self.get_total_users()
        if total_users == 0:
            return 100
        submitted_count = self.get_submitted_count()
        return int((submitted_count / total_users) * 100)


class Timesheet(models.Model):
    """
    Main Timesheet model for NovaTime.

    Represents a user's timesheet for a specific period,
    containing time entries and approval status.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='timesheets',
        help_text=_('User this timesheet belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheets',
        help_text=_('Workspace this timesheet belongs to')
    )

    period = models.ForeignKey(
        TimesheetPeriod,
        on_delete=models.CASCADE,
        related_name='timesheets',
        help_text=_('Timesheet period this belongs to')
    )

    # Timesheet details
    title = models.CharField(
        _('title'),
        max_length=200,
        blank=True,
        help_text=_('Optional title for the timesheet')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('auto_approved', 'Auto Approved'),
        ],
        default='draft',
        help_text=_('Current status of the timesheet')
    )

    # Time calculations
    total_hours = models.DecimalField(
        _('total hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Total hours in this timesheet')
    )

    billable_hours = models.DecimalField(
        _('billable hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Billable hours in this timesheet')
    )

    total_cost = models.DecimalField(
        _('total cost'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Total cost for this timesheet')
    )

    # Approval workflow
    submitted_at = models.DateTimeField(
        _('submitted at'),
        null=True,
        blank=True,
        help_text=_('When the timesheet was submitted')
    )

    approved_at = models.DateTimeField(
        _('approved at'),
        null=True,
        blank=True,
        help_text=_('When the timesheet was approved')
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_timesheets',
        help_text=_('User who approved this timesheet')
    )

    rejection_reason = models.TextField(
        _('rejection reason'),
        blank=True,
        help_text=_('Reason for rejection if applicable')
    )

    # Approval workflow settings
    approval_workflow = models.ForeignKey(
        'ApprovalWorkflow',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timesheets',
        help_text=_('Approval workflow for this timesheet')
    )

    # Quality metrics
    quality_score = models.FloatField(
        _('quality score'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('AI-calculated quality score (0-100)')
    )

    quality_issues = models.JSONField(
        _('quality issues'),
        default=list,
        help_text=_('List of quality issues found')
    )

    # AI features
    ai_generated = models.BooleanField(
        _('AI generated'),
        default=False,
        help_text=_('Whether this timesheet was AI-generated')
    )

    ai_suggestions = models.JSONField(
        _('AI suggestions'),
        default=list,
        help_text=_('AI suggestions for this timesheet')
    )

    # Custom fields and metadata
    custom_fields = models.JSONField(
        _('custom fields'),
        default=dict,
        help_text=_('Custom fields specific to this timesheet')
    )

    # Metadata
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this timesheet is active')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', '-period__start_date']
        verbose_name = _('timesheet')
        verbose_name_plural = _('timesheets')
        unique_together = ['user', 'period']

    def __str__(self):
        period_name = f"{self.period.start_date} - {self.period.end_date}"
        return f"{self.user.get_full_name()}: {period_name} ({self.status})"

    def save(self, *args, **kwargs):
        """Calculate totals when saving."""
        if self.pk:  # Only calculate for existing timesheets
            self._calculate_totals()
        super().save(*args, **kwargs)

    def _calculate_totals(self):
        """Calculate total hours, billable hours, and cost."""
        # Get all time entries for this timesheet's period
        time_entries = self.entries.filter(
            time_entry__is_active=True,
            time_entry__approval_status__in=['approved', 'auto_approved']
        )

        # Calculate totals
        total_minutes = sum(
            entry.time_entry.duration_minutes
            for entry in time_entries
            if entry.time_entry.duration_minutes
        )

        billable_minutes = sum(
            entry.time_entry.duration_minutes
            for entry in time_entries
            if entry.time_entry.duration_minutes and entry.time_entry.is_billable
        )

        total_cost = sum(
            entry.time_entry.cost_amount
            for entry in time_entries
            if entry.time_entry.cost_amount
        )

        # Convert to hours and update
        self.total_hours = total_minutes / 60
        self.billable_hours = billable_minutes / 60
        self.total_cost = total_cost

    def submit(self):
        """Submit the timesheet for approval."""
        from django.utils import timezone

        if self.status != 'draft':
            raise ValueError("Only draft timesheets can be submitted")

        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()

        # TODO: Trigger approval workflow
        # self._start_approval_workflow()

    def approve(self, approved_by):
        """Approve the timesheet."""
        from django.utils import timezone

        if self.status not in ['submitted', 'draft']:
            raise ValueError("Only submitted or draft timesheets can be approved")

        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()

    def reject(self, approved_by, reason=''):
        """Reject the timesheet."""
        if self.status != 'submitted':
            raise ValueError("Only submitted timesheets can be rejected")

        self.status = 'rejected'
        self.approved_by = approved_by
        self.rejection_reason = reason
        self.save()

    def get_completion_percentage(self):
        """Get completion percentage based on expected vs actual hours."""
        # This is a simplified calculation - in practice, you'd have
        # more sophisticated logic based on user contracts, etc.
        if self.total_hours == 0:
            return 0

        # Assume 40 hours is expected for weekly periods
        expected_hours = 40 if self.period.period_type == 'weekly' else 160
        return min(int((self.total_hours / expected_hours) * 100), 100)

    def get_quality_issues(self):
        """Get list of quality issues."""
        issues = []

        # Check for missing descriptions
        entries_without_description = self.entries.filter(
            time_entry__description__isnull=True
        ).count()

        if entries_without_description > 0:
            issues.append({
                'type': 'missing_descriptions',
                'count': entries_without_description,
                'message': f"{entries_without_description} entries missing descriptions"
            })

        # Check for unusually long entries
        long_entries = self.entries.filter(
            time_entry__duration_minutes__gt=480  # 8 hours
        ).count()

        if long_entries > 0:
            issues.append({
                'type': 'long_entries',
                'count': long_entries,
                'message': f"{long_entries} entries longer than 8 hours"
            })

        return issues


class TimesheetEntry(models.Model):
    """
    Linking model between Timesheets and TimeEntries.

    Allows time entries to be included in specific timesheets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='entries',
        help_text=_('Timesheet this entry belongs to')
    )

    time_entry = models.ForeignKey(
        'time_entries.TimeEntry',
        on_delete=models.CASCADE,
        related_name='timesheet_entries',
        help_text=_('Time entry included in this timesheet')
    )

    # Entry-specific metadata
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Notes specific to this timesheet entry')
    )

    # Billing adjustments
    adjusted_hours = models.DecimalField(
        _('adjusted hours'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Adjusted hours for this entry in the timesheet')
    )

    adjusted_rate = models.DecimalField(
        _('adjusted rate'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Adjusted hourly rate for this entry')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['timesheet', 'time_entry']
        ordering = ['created_at']
        verbose_name = _('timesheet entry')
        verbose_name_plural = _('timesheet entries')

    def __str__(self):
        return f"{self.timesheet}: {self.time_entry}"

    def get_effective_hours(self):
        """Get effective hours (adjusted or original)."""
        if self.adjusted_hours is not None:
            return self.adjusted_hours
        return self.time_entry.duration_minutes / 60 if self.time_entry.duration_minutes else 0

    def get_effective_rate(self):
        """Get effective rate (adjusted or original)."""
        if self.adjusted_rate is not None:
            return self.adjusted_rate
        return self.time_entry.hourly_rate or 0


class ApprovalWorkflow(models.Model):
    """
    Approval workflow model for defining approval processes.

    Defines the steps and rules for timesheet approvals.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='approval_workflows',
        help_text=_('Workspace this workflow belongs to')
    )

    name = models.CharField(
        _('workflow name'),
        max_length=200,
        help_text=_('Display name for the workflow')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Optional description of the workflow')
    )

    # Workflow configuration
    workflow_type = models.CharField(
        _('workflow type'),
        max_length=20,
        choices=[
            ('sequential', 'Sequential'),
            ('parallel', 'Parallel'),
            ('hierarchical', 'Hierarchical'),
        ],
        default='sequential',
        help_text=_('Type of approval workflow')
    )

    # Approval steps
    steps = models.JSONField(
        _('steps'),
        default=list,
        help_text=_('List of approval steps with approvers and conditions')
    )

    # Conditions and rules
    conditions = models.JSONField(
        _('conditions'),
        default=dict,
        help_text=_('Conditions that must be met for approval')
    )

    # Auto-approval rules
    auto_approve_rules = models.JSONField(
        _('auto-approve rules'),
        default=list,
        help_text=_('Rules for automatic approval')
    )

    # Metadata
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this workflow is active')
    )

    is_default = models.BooleanField(
        _('default'),
        default=False,
        help_text=_('Whether this is the default workflow for the workspace')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_approval_workflows',
        help_text=_('User who created this workflow')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workspace', 'name']
        verbose_name = _('approval workflow')
        verbose_name_plural = _('approval workflows')

    def __str__(self):
        return f"{self.workspace.name}: {self.name}"


class TimesheetComment(models.Model):
    """
    Comment model for timesheet discussions and approval feedback.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text=_('Timesheet this comment belongs to')
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='timesheet_comments',
        help_text=_('User who wrote this comment')
    )

    content = models.TextField(
        _('content'),
        help_text=_('Comment content')
    )

    # Comment type
    comment_type = models.CharField(
        _('comment type'),
        max_length=20,
        choices=[
            ('comment', 'Comment'),
            ('approval_request', 'Approval Request'),
            ('approval_feedback', 'Approval Feedback'),
            ('rejection_reason', 'Rejection Reason'),
            ('system', 'System Update'),
        ],
        default='comment',
        help_text=_('Type of comment')
    )

    # Visibility
    is_private = models.BooleanField(
        _('private'),
        default=False,
        help_text=_('Whether this comment is private to approvers')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('timesheet comment')
        verbose_name_plural = _('timesheet comments')

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.timesheet}"


class TimesheetTemplate(models.Model):
    """
    Template model for creating timesheets with predefined settings.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheet_templates',
        help_text=_('Workspace this template belongs to')
    )

    name = models.CharField(
        _('template name'),
        max_length=200,
        help_text=_('Display name for the template')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Optional description of the template')
    )

    # Template data
    template_data = models.JSONField(
        _('template data'),
        help_text=_('JSON representation of timesheet fields to pre-populate')
    )

    # Template settings
    auto_include_entries = models.BooleanField(
        _('auto-include entries'),
        default=True,
        help_text=_('Whether to automatically include time entries')
    )

    include_rules = models.JSONField(
        _('include rules'),
        default=dict,
        help_text=_('Rules for which time entries to include')
    )

    # Usage tracking
    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this template has been used')
    )

    # Metadata
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the template is available for use')
    )

    is_public = models.BooleanField(
        _('public'),
        default=False,
        help_text=_('Whether this template is available to all workspace members')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_timesheet_templates',
        help_text=_('User who created this template')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workspace', 'name']
        verbose_name = _('timesheet template')
        verbose_name_plural = _('timesheet templates')

    def __str__(self):
        return f"{self.workspace.name}: {self.name}"