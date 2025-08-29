from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta


def default_dict():
    """Default empty dictionary"""
    return {}


class Timesheet(models.Model):
    """
    Weekly/bi-weekly timesheet aggregation.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
    ]
    
    PERIOD_TYPES = [
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and organization
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='timesheets'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheets'
    )
    
    # Time period
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='weekly')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Time totals (calculated from time entries)
    total_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    billable_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    overtime_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # AI assistance
    ai_generated = models.BooleanField(default=False)
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    ai_suggestions_count = models.PositiveIntegerField(default=0)
    ai_accepted_count = models.PositiveIntegerField(default=0)
    
    # Submission tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_timesheets'
    )
    
    # Approval tracking
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_timesheets'
    )
    
    # Notes and comments
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timesheets'
        unique_together = ['user', 'start_date', 'end_date']
        indexes = [
            models.Index(fields=['user', 'start_date']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['status', 'submitted_at']),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.start_date} to {self.end_date}"


class TimesheetEntry(models.Model):
    """
    Individual day entries within a timesheet.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    
    # Date and project
    date = models.DateField()
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='timesheet_entries'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timesheet_entries'
    )
    
    # Time details
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    
    # Rates and billing
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Source tracking
    source_time_entries = models.ManyToManyField(
        'time_entries.TimeEntry',
        blank=True,
        related_name='timesheet_entries'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timesheet_entries'
        unique_together = ['timesheet', 'date', 'project', 'task']
        
    def save(self, *args, **kwargs):
        # Calculate total amount if hourly rate is set
        if self.hourly_rate and self.hours:
            self.total_amount = self.hourly_rate * self.hours
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.timesheet.user.email} - {self.date} - {self.project.name}: {self.hours}h"


class TimesheetApproval(models.Model):
    """
    Approval workflow for timesheets.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    
    # Approver details
    approver = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='timesheet_approvals'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval details
    comments = models.TextField(blank=True)
    approved_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'timesheet_approvals'
        unique_together = ['timesheet', 'approver']
        
    def __str__(self):
        return f"{self.timesheet} approval by {self.approver.email} ({self.status})"


class TimesheetException(models.Model):
    """
    Exceptions and issues flagged in timesheets.
    """
    EXCEPTION_TYPES = [
        ('overtime', 'Overtime Hours'),
        ('missing_time', 'Missing Time'),
        ('duplicate_entry', 'Duplicate Entry'),
        ('rate_mismatch', 'Rate Mismatch'),
        ('policy_violation', 'Policy Violation'),
        ('ai_flagged', 'AI Flagged'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='exceptions'
    )
    
    exception_type = models.CharField(max_length=20, choices=EXCEPTION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Exception details
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # AI detection details
    ai_detected = models.BooleanField(default=False)
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Resolution
    resolved_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_exceptions'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'timesheet_exceptions'
        indexes = [
            models.Index(fields=['timesheet', 'status']),
            models.Index(fields=['severity', 'status']),
        ]
        
    def __str__(self):
        return f"{self.timesheet} - {self.exception_type} ({self.severity})"


class TimesheetTemplate(models.Model):
    """
    Templates for recurring timesheet patterns.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='timesheet_templates'
    )
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='timesheet_templates'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Template data
    template_data = models.JSONField(default=default_dict)  # Project/task/hour patterns
    
    # Usage tracking
    is_active = models.BooleanField(default=True)
    use_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timesheet_templates'
        unique_together = ['user', 'name']
        
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class TimesheetReminder(models.Model):
    """
    Reminders for timesheet submission.
    """
    REMINDER_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('overdue', 'Overdue'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='timesheet_reminders'
    )
    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Reminder content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'timesheet_reminders'
        
    def __str__(self):
        return f"{self.reminder_type} reminder for {self.user.email}"
