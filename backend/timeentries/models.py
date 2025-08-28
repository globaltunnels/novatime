"""
Time entries models for NovaTime.

This app handles time tracking, timer functionality, approvals,
idle detection, and time entry management.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal


class TimeEntry(models.Model):
    """
    TimeEntry model for recording time spent on tasks and projects.

    Represents a single time entry that can be manual or timer-based.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text=_('User who logged this time entry')
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text=_('Organization this time entry belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text=_('Workspace this time entry belongs to')
    )

    project = models.ForeignKey(
        'tasks.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text=_('Project this time entry belongs to')
    )

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text=_('Task this time entry belongs to')
    )

    # Time tracking
    start_time = models.DateTimeField(
        _('start time'),
        help_text=_('When the time entry started')
    )

    end_time = models.DateTimeField(
        _('end time'),
        null=True,
        blank=True,
        help_text=_('When the time entry ended')
    )

    duration_minutes = models.PositiveIntegerField(
        _('duration in minutes'),
        default=0,
        help_text=_('Duration of the time entry in minutes')
    )

    # Description and details
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the work done')
    )

    entry_type = models.CharField(
        _('entry type'),
        max_length=20,
        choices=[
            ('manual', 'Manual Entry'),
            ('timer', 'Timer'),
            ('mobile', 'Mobile App'),
            ('kiosk', 'Kiosk'),
            ('integration', 'Integration'),
            ('ai_generated', 'AI Generated'),
        ],
        default='manual',
        help_text=_('How this time entry was created')
    )

    # Billing and rates
    is_billable = models.BooleanField(
        _('billable'),
        default=True,
        help_text=_('Whether this time entry is billable')
    )

    hourly_rate = models.DecimalField(
        _('hourly rate'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Hourly rate for this time entry')
    )

    cost_amount = models.DecimalField(
        _('cost amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Calculated cost for this time entry')
    )

    # Location and context
    location = models.CharField(
        _('location'),
        max_length=255,
        blank=True,
        help_text=_('Location where the work was done')
    )

    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address of the user when logging time')
    )

    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        help_text=_('Browser/client user agent')
    )

    # Status and approval
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('locked', 'Locked'),
        ],
        default='draft',
        help_text=_('Current status of the time entry')
    )

    submitted_at = models.DateTimeField(
        _('submitted at'),
        null=True,
        blank=True,
        help_text=_('When the time entry was submitted for approval')
    )

    approved_at = models.DateTimeField(
        _('approved at'),
        null=True,
        blank=True,
        help_text=_('When the time entry was approved')
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_entries',
        help_text=_('User who approved this time entry')
    )

    rejection_reason = models.TextField(
        _('rejection reason'),
        blank=True,
        help_text=_('Reason for rejection if applicable')
    )

    # Tags and categorization
    tags = models.JSONField(
        _('tags'),
        default=list,
        blank=True,
        help_text=_('Tags associated with this time entry')
    )

    categories = models.JSONField(
        _('categories'),
        default=list,
        blank=True,
        help_text=_('Categories for this time entry')
    )

    # Custom fields
    custom_fields = models.JSONField(
        _('custom fields'),
        default=dict,
        blank=True,
        help_text=_('Custom fields for additional time entry data')
    )

    # Integration data
    integration_data = models.JSONField(
        _('integration data'),
        default=dict,
        blank=True,
        help_text=_('Data from external integrations')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = _('time entry')
        verbose_name_plural = _('time entries')
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['organization', 'start_time']),
            models.Index(fields=['workspace', 'start_time']),
            models.Index(fields=['project', 'start_time']),
            models.Index(fields=['task', 'start_time']),
            models.Index(fields=['status']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['is_billable']),
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        duration = f"{self.duration_minutes}min"
        if self.task:
            return f"{self.user.get_full_name()}: {self.task.title} ({duration})"
        elif self.project:
            return f"{self.user.get_full_name()}: {self.project.name} ({duration})"
        else:
            return f"{self.user.get_full_name()}: {self.description[:50]} ({duration})"

    def save(self, *args, **kwargs):
        """Save time entry and handle related calculations."""
        # Calculate duration if end_time is set
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = int(duration.total_seconds() / 60)

        # Calculate cost if hourly rate is set
        if self.hourly_rate and self.duration_minutes:
            hours = Decimal(self.duration_minutes) / 60
            self.cost_amount = (hours * self.hourly_rate).quantize(Decimal('0.01'))

        # Set submitted_at when status changes to submitted
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        elif self.status != 'submitted':
            self.submitted_at = None

        # Set approved_at when status changes to approved
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        elif self.status != 'approved':
            self.approved_at = None

        super().save(*args, **kwargs)

    def get_duration_hours(self):
        """Get duration in hours."""
        return Decimal(self.duration_minutes) / 60

    def get_cost(self):
        """Get calculated cost."""
        if self.cost_amount:
            return self.cost_amount
        elif self.hourly_rate and self.duration_minutes:
            hours = Decimal(self.duration_minutes) / 60
            return (hours * self.hourly_rate).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def is_running(self):
        """Check if this time entry is currently running."""
        return self.end_time is None

    def stop(self, end_time=None):
        """Stop the time entry."""
        if end_time:
            self.end_time = end_time
        else:
            self.end_time = timezone.now()
        self.save()

    def can_user_edit(self, user):
        """Check if user can edit this time entry."""
        # Owner can always edit
        if self.user == user:
            return True

        # Organization/workspace admins can edit
        if self.organization.users.filter(id=user.id).exists():
            # Check if user has admin role in workspace
            membership = self.workspace.memberships.filter(
                user=user,
                role__in=['owner', 'admin'],
                is_active=True
            ).first()
            if membership:
                return True

        return False

    def can_user_approve(self, user):
        """Check if user can approve this time entry."""
        # Organization/workspace admins can approve
        membership = self.workspace.memberships.filter(
            user=user,
            role__in=['owner', 'admin'],
            is_active=True
        ).first()
        return membership is not None

    def submit_for_approval(self):
        """Submit time entry for approval."""
        if self.status == 'draft':
            self.status = 'submitted'
            self.save()

    def approve(self, approved_by):
        """Approve the time entry."""
        if self.status == 'submitted':
            self.status = 'approved'
            self.approved_by = approved_by
            self.save()

    def reject(self, rejection_reason='', rejected_by=None):
        """Reject the time entry."""
        if self.status == 'submitted':
            self.status = 'rejected'
            self.rejection_reason = rejection_reason
            self.save()

    def lock(self):
        """Lock the time entry to prevent further edits."""
        self.status = 'locked'
        self.save()


class Timer(models.Model):
    """
    Timer model for active time tracking sessions.

    Represents a running timer that can be started, paused, and stopped.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='timers',
        help_text=_('User who owns this timer')
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='timers',
        help_text=_('Organization this timer belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timers',
        help_text=_('Workspace this timer belongs to')
    )

    project = models.ForeignKey(
        'tasks.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='timers',
        help_text=_('Project this timer is tracking')
    )

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='timers',
        help_text=_('Task this timer is tracking')
    )

    # Timer details
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the work being timed')
    )

    # Timing
    start_time = models.DateTimeField(
        _('start time'),
        help_text=_('When the timer was started')
    )

    end_time = models.DateTimeField(
        _('end time'),
        null=True,
        blank=True,
        help_text=_('When the timer was stopped')
    )

    paused_at = models.DateTimeField(
        _('paused at'),
        null=True,
        blank=True,
        help_text=_('When the timer was last paused')
    )

    total_paused_seconds = models.PositiveIntegerField(
        _('total paused seconds'),
        default=0,
        help_text=_('Total time the timer has been paused')
    )

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('paused', 'Paused'),
            ('stopped', 'Stopped'),
        ],
        default='running',
        help_text=_('Current status of the timer')
    )

    # Settings
    is_billable = models.BooleanField(
        _('billable'),
        default=True,
        help_text=_('Whether this timer session is billable')
    )

    hourly_rate = models.DecimalField(
        _('hourly rate'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Hourly rate for this timer session')
    )

    # Idle detection
    idle_threshold_minutes = models.PositiveIntegerField(
        _('idle threshold minutes'),
        default=5,
        help_text=_('Minutes of inactivity before considering idle')
    )

    last_activity_at = models.DateTimeField(
        _('last activity at'),
        default=timezone.now,
        help_text=_('Last recorded user activity')
    )

    # Location and context
    location = models.CharField(
        _('location'),
        max_length=255,
        blank=True,
        help_text=_('Location where the timer is running')
    )

    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address of the user running the timer')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = _('timer')
        verbose_name_plural = _('timers')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        duration = self.get_elapsed_time()
        if self.task:
            return f"{self.user.get_full_name()}: {self.task.title} ({duration})"
        elif self.project:
            return f"{self.user.get_full_name()}: {self.project.name} ({duration})"
        else:
            return f"{self.user.get_full_name()}: Timer ({duration})"

    def save(self, *args, **kwargs):
        """Save timer and handle related updates."""
        # Set start_time if not set
        if not self.start_time:
            self.start_time = timezone.now()

        super().save(*args, **kwargs)

    def get_elapsed_time(self):
        """Get elapsed time as a formatted string."""
        elapsed_seconds = self.get_elapsed_seconds()
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def get_elapsed_seconds(self):
        """Get elapsed time in seconds."""
        now = timezone.now()

        if self.status == 'stopped' and self.end_time:
            end_time = self.end_time
        else:
            end_time = now

        elapsed = end_time - self.start_time
        elapsed_seconds = int(elapsed.total_seconds())

        # Subtract paused time
        elapsed_seconds -= self.total_paused_seconds

        return max(0, elapsed_seconds)

    def get_elapsed_minutes(self):
        """Get elapsed time in minutes."""
        return self.get_elapsed_seconds() // 60

    def start(self):
        """Start the timer."""
        if self.status == 'stopped':
            self.status = 'running'
            self.start_time = timezone.now()
            self.end_time = None
            self.paused_at = None
            self.total_paused_seconds = 0
            self.save()

    def pause(self):
        """Pause the timer."""
        if self.status == 'running':
            self.status = 'paused'
            self.paused_at = timezone.now()
            self.save()

    def resume(self):
        """Resume the timer."""
        if self.status == 'paused' and self.paused_at:
            paused_duration = timezone.now() - self.paused_at
            self.total_paused_seconds += int(paused_duration.total_seconds())
            self.status = 'running'
            self.paused_at = None
            self.save()

    def stop(self, create_time_entry=True):
        """Stop the timer and optionally create a time entry."""
        if self.status in ['running', 'paused']:
            self.end_time = timezone.now()
            self.status = 'stopped'
            self.save()

            if create_time_entry:
                return self.create_time_entry()

    def create_time_entry(self):
        """Create a time entry from this timer."""
        if self.status != 'stopped' or not self.end_time:
            return None

        duration_minutes = self.get_elapsed_minutes()

        time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_minutes=duration_minutes,
            description=self.description,
            entry_type='timer',
            is_billable=self.is_billable,
            hourly_rate=self.hourly_rate,
            location=self.location,
            ip_address=self.ip_address,
            tags=self.get_tags(),
            categories=self.get_categories()
        )

        return time_entry

    def get_tags(self):
        """Get tags for this timer."""
        tags = []
        if self.project:
            tags.append(f"project:{self.project.slug}")
        if self.task:
            tags.append(f"task:{self.task.id}")
        return tags

    def get_categories(self):
        """Get categories for this timer."""
        categories = []
        if self.project:
            categories.append(self.project.project_type)
        return categories

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = timezone.now()
        self.save()

    def is_idle(self):
        """Check if timer is idle."""
        if self.status != 'running':
            return False

        idle_threshold = timedelta(minutes=self.idle_threshold_minutes)
        return (timezone.now() - self.last_activity_at) > idle_threshold

    def handle_idle(self):
        """Handle idle timer (pause or stop based on settings)."""
        if self.is_idle():
            # For now, just pause the timer
            self.pause()


class TimeEntryApproval(models.Model):
    """
    TimeEntryApproval model for managing approval workflows.

    Represents an approval request for time entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='time_entry_approvals',
        help_text=_('Organization this approval belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='time_entry_approvals',
        help_text=_('Workspace this approval belongs to')
    )

    approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='time_entry_approvals',
        help_text=_('User who needs to approve')
    )

    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='requested_time_entry_approvals',
        help_text=_('User who requested the approval')
    )

    # Time entries
    time_entries = models.ManyToManyField(
        TimeEntry,
        related_name='approvals',
        help_text=_('Time entries that need approval')
    )

    # Approval details
    approval_type = models.CharField(
        _('approval type'),
        max_length=20,
        choices=[
            ('weekly', 'Weekly Timesheet'),
            ('monthly', 'Monthly Report'),
            ('project', 'Project Hours'),
            ('custom', 'Custom Range'),
        ],
        default='weekly',
        help_text=_('Type of approval request')
    )

    period_start = models.DateField(
        _('period start'),
        help_text=_('Start date of the approval period')
    )

    period_end = models.DateField(
        _('period end'),
        help_text=_('End date of the approval period')
    )

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('partially_approved', 'Partially Approved'),
        ],
        default='pending',
        help_text=_('Current status of the approval')
    )

    # Comments and feedback
    approver_comments = models.TextField(
        _('approver comments'),
        blank=True,
        help_text=_('Comments from the approver')
    )

    requested_notes = models.TextField(
        _('requested notes'),
        blank=True,
        help_text=_('Notes from the person requesting approval')
    )

    # Timestamps
    requested_at = models.DateTimeField(
        _('requested at'),
        default=timezone.now,
        help_text=_('When the approval was requested')
    )

    responded_at = models.DateTimeField(
        _('responded at'),
        null=True,
        blank=True,
        help_text=_('When the approval was responded to')
    )

    # Statistics
    total_hours = models.DecimalField(
        _('total hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Total hours in this approval request')
    )

    billable_hours = models.DecimalField(
        _('billable hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Billable hours in this approval request')
    )

    total_entries = models.PositiveIntegerField(
        _('total entries'),
        default=0,
        help_text=_('Total number of time entries')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = _('time entry approval')
        verbose_name_plural = _('time entry approvals')
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['approver', 'status']),
            models.Index(fields=['requested_by', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['period_start']),
            models.Index(fields=['period_end']),
            models.Index(fields=['requested_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Approval for {self.requested_by.get_full_name()}: {self.period_start} - {self.period_end}"

    def save(self, *args, **kwargs):
        """Save approval and calculate statistics."""
        if self.pk:
            self._calculate_statistics()
        super().save(*args, **kwargs)

    def _calculate_statistics(self):
        """Calculate statistics for this approval."""
        time_entries = self.time_entries.all()

        self.total_entries = time_entries.count()

        total_minutes = time_entries.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        self.total_hours = Decimal(total_minutes) / 60

        billable_minutes = time_entries.filter(is_billable=True).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        self.billable_hours = Decimal(billable_minutes) / 60

    def approve(self, comments=''):
        """Approve the time entries."""
        if self.status == 'pending':
            self.status = 'approved'
            self.approver_comments = comments
            self.responded_at = timezone.now()

            # Update all time entries
            self.time_entries.update(
                status='approved',
                approved_at=self.responded_at,
                approved_by=self.approver
            )

            self.save()

    def reject(self, comments=''):
        """Reject the time entries."""
        if self.status == 'pending':
            self.status = 'rejected'
            self.approver_comments = comments
            self.responded_at = timezone.now()

            # Update all time entries
            self.time_entries.update(
                status='rejected'
            )

            self.save()

    def partially_approve(self, approved_entries, rejected_entries, comments=''):
        """Partially approve the time entries."""
        if self.status == 'pending':
            self.status = 'partially_approved'
            self.approver_comments = comments
            self.responded_at = timezone.now()

            # Update approved entries
            TimeEntry.objects.filter(id__in=approved_entries).update(
                status='approved',
                approved_at=self.responded_at,
                approved_by=self.approver
            )

            # Update rejected entries
            TimeEntry.objects.filter(id__in=rejected_entries).update(
                status='rejected'
            )

            self.save()


class IdlePeriod(models.Model):
    """
    IdlePeriod model for tracking user idle time.

    Represents periods of user inactivity that may affect time tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='idle_periods',
        help_text=_('User who was idle')
    )

    timer = models.ForeignKey(
        Timer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='idle_periods',
        help_text=_('Timer that was affected by idle time')
    )

    # Idle period details
    start_time = models.DateTimeField(
        _('start time'),
        help_text=_('When the idle period started')
    )

    end_time = models.DateTimeField(
        _('end time'),
        null=True,
        blank=True,
        help_text=_('When the idle period ended')
    )

    duration_seconds = models.PositiveIntegerField(
        _('duration in seconds'),
        default=0,
        help_text=_('Duration of the idle period in seconds')
    )

    # Reason and context
    reason = models.CharField(
        _('reason'),
        max_length=50,
        choices=[
            ('system_lock', 'System Lock'),
            ('screen_saver', 'Screen Saver'),
            ('user_inactive', 'User Inactive'),
            ('manual_pause', 'Manual Pause'),
            ('network_disconnect', 'Network Disconnect'),
        ],
        default='user_inactive',
        help_text=_('Reason for the idle period')
    )

    context_data = models.JSONField(
        _('context data'),
        default=dict,
        blank=True,
        help_text=_('Additional context about the idle period')
    )

    # Actions taken
    action_taken = models.CharField(
        _('action taken'),
        max_length=20,
        choices=[
            ('none', 'No Action'),
            ('paused_timer', 'Paused Timer'),
            ('stopped_timer', 'Stopped Timer'),
            ('created_idle_entry', 'Created Idle Entry'),
        ],
        default='none',
        help_text=_('Action taken in response to idle period')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        verbose_name = _('idle period')
        verbose_name_plural = _('idle periods')
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['timer', 'start_time']),
            models.Index(fields=['reason']),
            models.Index(fields=['action_taken']),
            models.Index(fields=['start_time']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        duration = f"{self.duration_seconds}s"
        return f"{self.user.get_full_name()}: Idle ({duration}) - {self.reason}"

    def save(self, *args, **kwargs):
        """Save idle period and calculate duration."""
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_seconds = int(duration.total_seconds())

        super().save(*args, **kwargs)

    def get_duration_minutes(self):
        """Get duration in minutes."""
        return self.duration_seconds // 60

    def is_active(self):
        """Check if idle period is currently active."""
        return self.end_time is None

    def stop(self, end_time=None):
        """Stop the idle period."""
        if end_time:
            self.end_time = end_time
        else:
            self.end_time = timezone.now()
        self.save()


class TimeEntryTemplate(models.Model):
    """
    TimeEntryTemplate model for reusable time entry templates.

    Represents templates for common time entry patterns.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Template name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Template description')
    )

    # Template data
    template_data = models.JSONField(
        _('template data'),
        help_text=_('JSON data containing template configuration')
    )

    # Visibility and usage
    is_public = models.BooleanField(
        _('public'),
        default=False,
        help_text=_('Whether this template is publicly available')
    )

    is_system = models.BooleanField(
        _('system template'),
        default=False,
        help_text=_('Whether this is a system-provided template')
    )

    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this template has been used')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_entry_templates',
        help_text=_('Organization this template belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_entry_templates',
        help_text=_('Workspace this template belongs to')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_time_entry_templates',
        help_text=_('User who created this template')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        verbose_name = _('time entry template')
        verbose_name_plural = _('time entry templates')
        indexes = [
            models.Index(fields=['organization', 'is_public']),
            models.Index(fields=['workspace', 'is_public']),
            models.Index(fields=['is_public']),
            models.Index(fields=['is_system']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Time Entry Template: {self.name}"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    def create_time_entry(self, user, **overrides):
        """Create a time entry from this template."""
        data = self.template_data.copy()
        data.update(overrides)

        time_entry = TimeEntry.objects.create(
            user=user,
            organization=data.get('organization'),
            workspace=data.get('workspace'),
            project=data.get('project'),
            task=data.get('task'),
            description=data.get('description', ''),
            entry_type='manual',
            is_billable=data.get('is_billable', True),
            hourly_rate=data.get('hourly_rate'),
            tags=data.get('tags', []),
            categories=data.get('categories', []),
            custom_fields=data.get('custom_fields', {})
        )

        self.increment_usage()
        return time_entry


class TimeEntryCategory(models.Model):
    """
    TimeEntryCategory model for categorizing time entries.

    Represents categories for organizing time entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Category name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Category description')
    )

    # Appearance
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#2563EB',
        help_text=_('Category color (hex code)')
    )

    icon = models.CharField(
        _('icon'),
        max_length=50,
        blank=True,
        help_text=_('Category icon')
    )

    # Usage
    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this category has been used')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='time_entry_categories',
        help_text=_('Organization this category belongs to')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_time_entry_categories',
        help_text=_('User who created this category')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('time entry category')
        verbose_name_plural = _('time entry categories')
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'usage_count']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.organization.name}: {self.name}"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class TimeEntryTag(models.Model):
    """
    TimeEntryTag model for tagging time entries.

    Represents tags for organizing and filtering time entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=50,
        help_text=_('Tag name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Tag description')
    )

    # Appearance
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#2563EB',
        help_text=_('Tag color (hex code)')
    )

    # Usage
    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this tag has been used')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='time_entry_tags',
        help_text=_('Organization this tag belongs to')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_time_entry_tags',
        help_text=_('User who created this tag')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('time entry tag')
        verbose_name_plural = _('time entry tags')
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'usage_count']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.organization.name}: {self.name}"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class TimeEntryComment(models.Model):
    """
    TimeEntryComment model for time entry discussions.

    Represents comments and discussions on time entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text=_('Time entry this comment belongs to')
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='time_entry_comments',
        help_text=_('User who wrote this comment')
    )

    # Comment content
    content = models.TextField(
        _('content'),
        help_text=_('Comment content')
    )

    # Threading
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text=_('Parent comment (for threaded replies)')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('time entry comment')
        verbose_name_plural = _('time entry comments')
        indexes = [
            models.Index(fields=['time_entry', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent_comment']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.author.get_full_name()}: {self.content[:50]}..."

    def get_replies(self):
        """Get all replies to this comment."""
        return TimeEntryComment.objects.filter(parent_comment=self)


class TimeEntryAttachment(models.Model):
    """
    TimeEntryAttachment model for time entry file attachments.

    Represents files attached to time entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_('Time entry this attachment belongs to')
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='time_entry_attachments',
        help_text=_('User who uploaded this attachment')
    )

    # File information
    file = models.FileField(
        _('file'),
        upload_to='time_entries/attachments/',
        help_text=_('Uploaded file')
    )

    filename = models.CharField(
        _('filename'),
        max_length=255,
        help_text=_('Original filename')
    )

    file_size = models.PositiveIntegerField(
        _('file size'),
        help_text=_('File size in bytes')
    )

    content_type = models.CharField(
        _('content type'),
        max_length=100,
        help_text=_('File content type')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('time entry attachment')
        verbose_name_plural = _('time entry attachments')
        indexes = [
            models.Index(fields=['time_entry', 'created_at']),
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['content_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.time_entry}: {self.filename}"


# Add reverse relationships
Timer.add_to_class(
    'time_entries',
    models.ManyToManyField(
        TimeEntry,
        through=TimeEntry,
        related_name='timers',
        help_text=_('Time entries created from this timer')
    )
)