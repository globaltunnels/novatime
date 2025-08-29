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


class TaskLabel(models.Model):
    """
    Labels/tags for categorizing tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='task_labels'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6b7280')  # Hex color
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_labels'
        unique_together = ['workspace', 'name']
        
    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Individual task/work item.
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('none', 'None'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Hierarchy
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    epic = models.ForeignKey(
        'projects.Epic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    sprint = models.ForeignKey(
        'projects.Sprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    
    # Task details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Time tracking
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assignee = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Organization
    labels = models.ManyToManyField(TaskLabel, blank=True, related_name='tasks')
    
    # AI-related fields
    ai_generated = models.BooleanField(default=False)
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    ai_metadata = models.JSONField(default=default_dict)  # AI processing metadata
    
    # External integrations
    external_id = models.CharField(max_length=255, blank=True)  # Jira, GitHub issue ID
    external_url = models.URLField(blank=True)
    
    # Ordering within lists
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assignee', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority', 'due_date']),
        ]
        
    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    """
    Task dependencies for project planning.
    """
    DEPENDENCY_TYPES = [
        ('blocks', 'Blocks'),
        ('blocked_by', 'Blocked By'),
        ('relates_to', 'Relates To'),
        ('duplicates', 'Duplicates'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependencies_from'
    )
    to_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependencies_to'
    )
    dependency_type = models.CharField(
        max_length=20,
        choices=DEPENDENCY_TYPES,
        default='blocks'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'task_dependencies'
        unique_together = ['from_task', 'to_task', 'dependency_type']
        
    def __str__(self):
        return f"{self.from_task.title} {self.dependency_type} {self.to_task.title}"


class TaskComment(models.Model):
    """
    Comments and updates on tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='task_comments'
    )
    
    content = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal team notes
    
    # Mentions and attachments
    mentions = models.ManyToManyField(
        'iam.User',
        blank=True,
        related_name='mentioned_in_comments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment on {self.task.title} by {self.author.email}"


class TaskActivity(models.Model):
    """
    Activity log for task changes.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('unassigned', 'Unassigned'),
        ('commented', 'Commented'),
        ('completed', 'Completed'),
        ('reopened', 'Reopened'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_activities'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    
    # Change details
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_activities'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.task.title} - {self.action} by {self.user}"


class TaskTemplate(models.Model):
    """
    Reusable task templates for common workflows.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='task_templates'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Template data
    title_template = models.CharField(max_length=255)
    description_template = models.TextField(blank=True)
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    default_priority = models.CharField(
        max_length=20,
        choices=Task.PRIORITY_CHOICES,
        default='medium'
    )
    default_labels = models.ManyToManyField(
        TaskLabel,
        blank=True,
        related_name='templates'
    )
    
    # Checklist for subtasks
    checklist = models.JSONField(default=default_list)  # List of subtask templates
    
    created_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_templates'
        unique_together = ['workspace', 'name']
        
    def __str__(self):
        return self.name
