from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


def default_dict():
    """Default empty dictionary"""
    return {}


def default_list():
    """Default empty list"""
    return []


class TimeEntry(models.Model):
    """
    Individual time tracking entry.
    """
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('timer', 'Timer'),
        ('import', 'Import'),
        ('ai_generated', 'AI Generated'),
        ('calendar_sync', 'Calendar Sync'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and organization context
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    
    # Work context
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries'
    )
    
    # Time tracking
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calculated duration in minutes"
    )
    
    # Entry details
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Source and status
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    is_running = models.BooleanField(default=False)  # Active timer
    is_locked = models.BooleanField(default=False)  # Approved/locked entries
    
    # AI-related fields
    ai_generated = models.BooleanField(default=False)
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    ai_source_data = models.JSONField(default=default_dict)  # Calendar event, commit, etc.
    
    # External integration
    external_id = models.CharField(max_length=255, blank=True)
    external_source = models.CharField(max_length=100, blank=True)  # 'calendar', 'jira', etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'time_entries'
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['project', 'start_time']),
            models.Index(fields=['workspace', 'start_time']),
            models.Index(fields=['is_running']),
        ]
        
    def save(self, *args, **kwargs):
        # Calculate duration if both start and end times are set
        if self.start_time and self.end_time and not self.is_running:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)
        
    def __str__(self):
        duration = f" ({self.duration_minutes}m)" if self.duration_minutes else ""
        return f"{self.user.email} - {self.project.name}{duration}"


class TimeEntryBreak(models.Model):
    """
    Breaks during time entries for accurate tracking.
    """
    BREAK_TYPES = [
        ('lunch', 'Lunch'),
        ('coffee', 'Coffee Break'),
        ('meeting', 'Meeting'),
        ('personal', 'Personal'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='breaks'
    )
    
    break_type = models.CharField(max_length=20, choices=BREAK_TYPES, default='other')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'time_entry_breaks'
        
    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.break_type} break - {self.duration_minutes}m"


class Timer(models.Model):
    """
    Active timer state for users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='active_timer'
    )
    
    # Current time entry being tracked
    time_entry = models.OneToOneField(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='timer'
    )
    
    # Timer state
    is_running = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_pause_duration = models.PositiveIntegerField(default=0)  # minutes
    
    # Last activity for idle detection
    last_activity = models.DateTimeField(auto_now=True)
    idle_threshold_minutes = models.PositiveIntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timers'
        
    def __str__(self):
        status = "paused" if self.is_paused else "running"
        return f"{self.user.email} timer ({status})"


class IdleTime(models.Model):
    """
    Tracked idle time for productivity insights.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='idle_periods'
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    
    # How idle time was detected
    detection_method = models.CharField(
        max_length=50,
        choices=[
            ('mouse_keyboard', 'Mouse/Keyboard Inactivity'),
            ('manual', 'Manual Report'),
            ('ai_detection', 'AI Detection'),
        ],
        default='mouse_keyboard'
    )
    
    # User action taken
    action_taken = models.CharField(
        max_length=50,
        choices=[
            ('keep', 'Keep Time'),
            ('discard', 'Discard Time'),
            ('pending', 'Pending Decision'),
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'idle_times'
        
    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Idle time: {self.duration_minutes}m ({self.action_taken})"


class TimeEntryCorrection(models.Model):
    """
    Audit trail for time entry modifications.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_entry = models.ForeignKey(
        TimeEntry,
        on_delete=models.CASCADE,
        related_name='corrections'
    )
    corrected_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='time_corrections'
    )
    
    # What was changed
    field_changed = models.CharField(max_length=100)
    old_value = models.JSONField()
    new_value = models.JSONField()
    reason = models.TextField(blank=True)
    
    # Approval if required
    requires_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_corrections'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'time_entry_corrections'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Correction to {self.time_entry} by {self.corrected_by}"


class BulkTimeOperation(models.Model):
    """
    Batch operations on time entries for efficiency.
    """
    OPERATION_TYPES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('bulk_edit', 'Bulk Edit'),
        ('ai_generation', 'AI Generation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='bulk_operations'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='bulk_operations'
    )
    
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Operation details
    total_entries = models.PositiveIntegerField(default=0)
    processed_entries = models.PositiveIntegerField(default=0)
    failed_entries = models.PositiveIntegerField(default=0)
    
    # Results
    result_data = models.JSONField(default=default_dict)  # Success/error details
    file_url = models.URLField(blank=True)  # For exports/imports
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bulk_time_operations'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.operation_type} operation by {self.user.email} ({self.status})"
