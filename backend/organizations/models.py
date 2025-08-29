from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


def default_work_days():
    """Default work days (Monday-Friday)"""
    return [1, 2, 3, 4, 5]


class Organization(models.Model):
    """
    Multi-tenant organization model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, blank=True)  # company.com
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    
    # Contact information
    phone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    email = models.EmailField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO country code
    
    # Settings
    timezone = models.CharField(max_length=50, default='UTC')
    business_hours_start = models.TimeField(default='09:00')
    business_hours_end = models.TimeField(default='17:00')
    work_days = models.JSONField(default=default_work_days)  # Mon-Fri
    
    # Subscription and billing
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise')
        ],
        default='free'
    )
    max_users = models.PositiveIntegerField(default=5)
    billing_email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        
    def __str__(self):
        return self.name


class Workspace(models.Model):
    """
    Workspace within an organization for team collaboration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='workspaces'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#2563eb')  # Hex color
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    
    # Time tracking settings
    require_project_for_time = models.BooleanField(default=True)
    allow_manual_time_entry = models.BooleanField(default=True)
    auto_stop_timers = models.BooleanField(default=True)
    idle_detection_minutes = models.PositiveIntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workspaces'
        unique_together = ['organization', 'name']
        
    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class Team(models.Model):
    """
    Team within a workspace.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace, 
        on_delete=models.CASCADE, 
        related_name='teams'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#22c55e')  # Hex color
    
    # Team lead
    lead = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='led_teams'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        unique_together = ['workspace', 'name']
        
    def __str__(self):
        return f"{self.workspace.name} - {self.name}"


class Membership(models.Model):
    """
    User membership in teams and workspaces.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('iam.User', on_delete=models.CASCADE, related_name='memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Employment details
    title = models.CharField(max_length=255, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weekly_capacity = models.PositiveIntegerField(default=40)  # hours per week
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'memberships'
        unique_together = ['user', 'workspace']
        
    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"


class Invitation(models.Model):
    """
    Invitation to join an organization/workspace.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    workspace = models.ForeignKey(
        Workspace, 
        on_delete=models.CASCADE, 
        related_name='invitations'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invitations'
    )
    role = models.CharField(max_length=20, choices=Membership.ROLE_CHOICES, default='member')
    
    invited_by = models.ForeignKey(
        'iam.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )
    message = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=255, unique=True)  # For secure invitation links
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Usually 7 days from creation
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'invitations'
        
    def __str__(self):
        return f"Invitation to {self.email} for {self.workspace.name}"
