from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Client(models.Model):
    """
    Client/Customer for billable projects.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='clients'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    
    # Billing settings
    default_hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    currency = models.CharField(max_length=3, default='USD')
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        unique_together = ['organization', 'name']
        
    def __str__(self):
        return self.name


class Project(models.Model):
    """
    Project container for tasks and time tracking.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    BILLING_TYPES = [
        ('hourly', 'Hourly'),
        ('fixed', 'Fixed Price'),
        ('non_billable', 'Non-Billable'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color
    
    # Status and timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Project management
    manager = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_projects'
    )
    
    # Billing configuration
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPES, default='hourly')
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    fixed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    budget_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Tracking settings
    require_time_entry_notes = models.BooleanField(default=False)
    track_expenses = models.BooleanField(default=False)
    
    # Template settings
    is_template = models.BooleanField(default=False)
    template_name = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        unique_together = ['workspace', 'name']
        
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"


class ProjectMember(models.Model):
    """
    Project team member assignments.
    """
    ROLE_CHOICES = [
        ('manager', 'Project Manager'),
        ('lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('qa', 'QA Tester'),
        ('member', 'Team Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        'iam.User',
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Billing rate override for this project
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Capacity allocation (percentage)
    allocation_percent = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_members'
        unique_together = ['project', 'user']
        
    def __str__(self):
        return f"{self.project.name} - {self.user.email} ({self.role})"


class Epic(models.Model):
    """
    Large feature or project phase container for tasks.
    """
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='epics'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog')
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Estimates
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Ordering
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'epics'
        ordering = ['order', 'created_at']
        
    def __str__(self):
        return f"{self.project.name} - {self.title}"


class Sprint(models.Model):
    """
    Sprint/iteration for agile project management.
    """
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sprints'
    )
    
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Capacity planning
    planned_capacity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total planned hours for this sprint"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sprints'
        unique_together = ['project', 'name']
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.project.name} - {self.name}"
