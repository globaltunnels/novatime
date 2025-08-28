"""
Organizations models for NovaTime.

This app handles multi-tenant organization management, workspaces,
teams, memberships, and organizational structure.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class Organization(models.Model):
    """
    Organization model for multi-tenant architecture.

    Represents a company, agency, or organization that uses NovaTime.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Organization name')
    )

    slug = models.SlugField(
        _('slug'),
        max_length=100,
        unique=True,
        help_text=_('URL-friendly identifier')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Organization description')
    )

    # Contact information
    website = models.URLField(
        _('website'),
        blank=True,
        help_text=_('Organization website')
    )

    email = models.EmailField(
        _('email'),
        blank=True,
        help_text=_('Primary contact email')
    )

    phone = models.CharField(
        _('phone'),
        max_length=20,
        blank=True,
        help_text=_('Primary contact phone')
    )

    # Address
    address_line_1 = models.CharField(
        _('address line 1'),
        max_length=255,
        blank=True,
        help_text=_('Street address')
    )

    address_line_2 = models.CharField(
        _('address line 2'),
        max_length=255,
        blank=True,
        help_text=_('Address line 2')
    )

    city = models.CharField(
        _('city'),
        max_length=100,
        blank=True,
        help_text=_('City')
    )

    state_province = models.CharField(
        _('state/province'),
        max_length=100,
        blank=True,
        help_text=_('State or province')
    )

    postal_code = models.CharField(
        _('postal code'),
        max_length=20,
        blank=True,
        help_text=_('Postal code')
    )

    country = models.CharField(
        _('country'),
        max_length=100,
        blank=True,
        help_text=_('Country')
    )

    # Business information
    industry = models.CharField(
        _('industry'),
        max_length=100,
        blank=True,
        choices=[
            ('technology', 'Technology'),
            ('consulting', 'Consulting'),
            ('marketing', 'Marketing'),
            ('finance', 'Finance'),
            ('healthcare', 'Healthcare'),
            ('education', 'Education'),
            ('manufacturing', 'Manufacturing'),
            ('retail', 'Retail'),
            ('construction', 'Construction'),
            ('other', 'Other'),
        ],
        help_text=_('Primary industry')
    )

    company_size = models.CharField(
        _('company size'),
        max_length=20,
        blank=True,
        choices=[
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('201-500', '201-500 employees'),
            ('501-1000', '501-1000 employees'),
            ('1000+', '1000+ employees'),
        ],
        help_text=_('Company size range')
    )

    # Branding
    logo_url = models.URLField(
        _('logo URL'),
        blank=True,
        help_text=_('Organization logo URL')
    )

    primary_color = models.CharField(
        _('primary color'),
        max_length=7,
        default='#2563EB',
        help_text=_('Primary brand color (hex code)')
    )

    secondary_color = models.CharField(
        _('secondary color'),
        max_length=7,
        default='#22C55E',
        help_text=_('Secondary brand color (hex code)')
    )

    # Settings
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='UTC',
        help_text=_('Default timezone for the organization')
    )

    date_format = models.CharField(
        _('date format'),
        max_length=20,
        default='YYYY-MM-DD',
        help_text=_('Default date format')
    )

    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('Default currency (ISO 4217 code)')
    )

    language = models.CharField(
        _('language'),
        max_length=10,
        default='en',
        help_text=_('Default language (ISO 639-1 code)')
    )

    # Subscription and billing
    subscription_plan = models.CharField(
        _('subscription plan'),
        max_length=50,
        default='free',
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        help_text=_('Current subscription plan')
    )

    subscription_status = models.CharField(
        _('subscription status'),
        max_length=20,
        default='active',
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('cancelled', 'Cancelled'),
            ('past_due', 'Past Due'),
            ('trial', 'Trial'),
        ],
        help_text=_('Subscription status')
    )

    trial_end_date = models.DateTimeField(
        _('trial end date'),
        null=True,
        blank=True,
        help_text=_('When the trial period ends')
    )

    # Limits and quotas
    max_users = models.PositiveIntegerField(
        _('max users'),
        default=10,
        help_text=_('Maximum number of users allowed')
    )

    max_projects = models.PositiveIntegerField(
        _('max projects'),
        default=5,
        help_text=_('Maximum number of projects allowed')
    )

    max_storage_gb = models.PositiveIntegerField(
        _('max storage (GB)'),
        default=1,
        help_text=_('Maximum storage allowed in GB')
    )

    # Features and permissions
    features_enabled = models.JSONField(
        _('features enabled'),
        default=dict,
        blank=True,
        help_text=_('Enabled features and their settings')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the organization is active')
    )

    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the organization is verified')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_organizations',
        help_text=_('User who created this organization')
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_organizations',
        help_text=_('Current owner of this organization')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['subscription_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save organization and handle related updates."""
        # Set owner as creator if not set
        if not self.owner and self.created_by:
            self.owner = self.created_by

        super().save(*args, **kwargs)

    def get_members_count(self):
        """Get total number of members across all workspaces."""
        return self.memberships.filter(is_active=True).count()

    def get_active_users_count(self):
        """Get number of active users."""
        return self.users.filter(
            memberships__is_active=True,
            memberships__organization=self
        ).distinct().count()

    def get_projects_count(self):
        """Get total number of projects across all workspaces."""
        return self.workspaces.aggregate(
            total_projects=models.Count('projects')
        )['total_projects'] or 0

    def get_workspaces_count(self):
        """Get number of workspaces."""
        return self.workspaces.count()

    def add_member(self, user, role='member', workspaces=None):
        """Add a user to the organization."""
        membership, created = OrganizationMembership.objects.get_or_create(
            organization=self,
            user=user,
            defaults={'role': role}
        )

        if created and workspaces:
            for workspace in workspaces:
                WorkspaceMembership.objects.get_or_create(
                    workspace=workspace,
                    user=user,
                    defaults={'role': role}
                )

        return membership, created

    def remove_member(self, user):
        """Remove a user from the organization."""
        memberships = OrganizationMembership.objects.filter(
            organization=self,
            user=user
        )
        count = memberships.count()
        memberships.delete()
        return count > 0

    def has_feature(self, feature_name):
        """Check if organization has a specific feature enabled."""
        return self.features_enabled.get(feature_name, False)

    def enable_feature(self, feature_name, settings=None):
        """Enable a feature for the organization."""
        if settings is None:
            settings = {}
        self.features_enabled[feature_name] = settings
        self.save(update_fields=['features_enabled'])

    def disable_feature(self, feature_name):
        """Disable a feature for the organization."""
        if feature_name in self.features_enabled:
            del self.features_enabled[feature_name]
            self.save(update_fields=['features_enabled'])

    def is_within_limits(self, resource_type, current_count):
        """Check if organization is within resource limits."""
        limits = {
            'users': self.max_users,
            'projects': self.max_projects,
        }

        limit = limits.get(resource_type)
        if limit is None:
            return True

        return current_count < limit

    def get_storage_usage_gb(self):
        """Get current storage usage in GB."""
        # This would calculate actual storage usage
        # For now, return a placeholder
        return 0.0

    def can_create_workspace(self):
        """Check if organization can create more workspaces."""
        # Implement workspace limits based on subscription
        return True

    def get_subscription_limits(self):
        """Get subscription limits for the organization."""
        limits = {
            'free': {
                'max_users': 3,
                'max_projects': 2,
                'max_storage_gb': 1,
                'features': ['basic_time_tracking', 'basic_reporting']
            },
            'starter': {
                'max_users': 25,
                'max_projects': 10,
                'max_storage_gb': 10,
                'features': ['time_tracking', 'reporting', 'basic_integrations']
            },
            'professional': {
                'max_users': 100,
                'max_projects': 50,
                'max_storage_gb': 100,
                'features': ['advanced_time_tracking', 'advanced_reporting', 'integrations', 'api_access']
            },
            'enterprise': {
                'max_users': -1,  # Unlimited
                'max_projects': -1,
                'max_storage_gb': -1,
                'features': ['all_features', 'custom_integrations', 'dedicated_support']
            }
        }

        return limits.get(self.subscription_plan, limits['free'])


class Workspace(models.Model):
    """
    Workspace model for organizing work within organizations.

    Represents a team, department, or project group within an organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Workspace name')
    )

    slug = models.SlugField(
        _('slug'),
        max_length=100,
        help_text=_('URL-friendly identifier')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Workspace description')
    )

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='workspaces',
        help_text=_('Organization this workspace belongs to')
    )

    # Settings
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        blank=True,
        help_text=_('Workspace timezone (defaults to organization)')
    )

    currency = models.CharField(
        _('currency'),
        max_length=3,
        blank=True,
        help_text=_('Workspace currency (defaults to organization)')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the workspace is active')
    )

    is_private = models.BooleanField(
        _('private'),
        default=False,
        help_text=_('Whether the workspace is private')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_workspaces',
        help_text=_('User who created this workspace')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('workspace')
        verbose_name_plural = _('workspaces')
        unique_together = ['organization', 'slug']
        indexes = [
            models.Index(fields=['organization', 'slug']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.organization.name}: {self.name}"

    def save(self, *args, **kwargs):
        """Save workspace and handle related updates."""
        # Inherit organization settings if not set
        if not self.timezone:
            self.timezone = self.organization.timezone
        if not self.currency:
            self.currency = self.organization.currency

        super().save(*args, **kwargs)

    def get_members_count(self):
        """Get number of active members."""
        return self.memberships.filter(is_active=True).count()

    def get_projects_count(self):
        """Get number of projects in this workspace."""
        return self.projects.count()

    def get_tasks_count(self):
        """Get total number of tasks across all projects."""
        return self.projects.aggregate(
            total_tasks=models.Count('tasks')
        )['total_tasks'] or 0

    def add_member(self, user, role='member'):
        """Add a user to the workspace."""
        membership, created = WorkspaceMembership.objects.get_or_create(
            workspace=self,
            user=user,
            defaults={'role': role}
        )
        return membership, created

    def remove_member(self, user):
        """Remove a user from the workspace."""
        memberships = WorkspaceMembership.objects.filter(
            workspace=self,
            user=user
        )
        count = memberships.count()
        memberships.delete()
        return count > 0

    def can_user_access(self, user):
        """Check if user can access this workspace."""
        if self.is_private:
            return self.memberships.filter(
                user=user,
                is_active=True
            ).exists()
        else:
            # Public workspace - any organization member can access
            return self.organization.memberships.filter(
                user=user,
                is_active=True
            ).exists()

    def get_user_role(self, user):
        """Get user's role in this workspace."""
        membership = self.memberships.filter(
            user=user,
            is_active=True
        ).first()
        return membership.role if membership else None


class Team(models.Model):
    """
    Team model for organizing users within workspaces.

    Represents a team, squad, or group within a workspace.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Team name')
    )

    slug = models.SlugField(
        _('slug'),
        max_length=100,
        help_text=_('URL-friendly identifier')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Team description')
    )

    # Relationships
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='teams',
        help_text=_('Workspace this team belongs to')
    )

    # Team lead
    lead = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_teams',
        help_text=_('Team lead')
    )

    # Settings
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#2563EB',
        help_text=_('Team color (hex code)')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the team is active')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_teams',
        help_text=_('User who created this team')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('team')
        verbose_name_plural = _('teams')
        unique_together = ['workspace', 'slug']
        indexes = [
            models.Index(fields=['workspace', 'slug']),
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.workspace.name}: {self.name}"

    def get_members_count(self):
        """Get number of team members."""
        return self.memberships.count()

    def add_member(self, user, role='member'):
        """Add a user to the team."""
        membership, created = TeamMembership.objects.get_or_create(
            team=self,
            user=user,
            defaults={'role': role}
        )
        return membership, created

    def remove_member(self, user):
        """Remove a user from the team."""
        memberships = TeamMembership.objects.filter(
            team=self,
            user=user
        )
        count = memberships.count()
        memberships.delete()
        return count > 0


class OrganizationMembership(models.Model):
    """
    OrganizationMembership model for organization-level permissions.

    Represents a user's membership in an organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text=_('Organization')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        help_text=_('User')
    )

    # Permissions
    role = models.CharField(
        _('role'),
        max_length=20,
        default='member',
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
            ('viewer', 'Viewer'),
        ],
        help_text=_('User role in the organization')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the membership is active')
    )

    # Permissions
    permissions = models.JSONField(
        _('permissions'),
        default=dict,
        blank=True,
        help_text=_('Custom permissions for this membership')
    )

    # Metadata
    invited_at = models.DateTimeField(
        _('invited at'),
        default=timezone.now,
        help_text=_('When the user was invited')
    )

    joined_at = models.DateTimeField(
        _('joined at'),
        null=True,
        blank=True,
        help_text=_('When the user joined')
    )

    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
        help_text=_('User who sent the invitation')
    )

    class Meta:
        ordering = ['-joined_at']
        verbose_name = _('organization membership')
        verbose_name_plural = _('organization memberships')
        unique_together = ['organization', 'user']
        indexes = [
            models.Index(fields=['organization', 'user']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['invited_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.organization.name} ({self.role})"

    def save(self, *args, **kwargs):
        """Save membership and handle related updates."""
        if self.is_active and not self.joined_at:
            self.joined_at = timezone.now()

        super().save(*args, **kwargs)

    def has_permission(self, permission):
        """Check if membership has a specific permission."""
        # Check role-based permissions
        role_permissions = {
            'owner': ['all'],
            'admin': ['manage_users', 'manage_workspaces', 'manage_billing', 'view_reports'],
            'member': ['create_projects', 'manage_own_tasks', 'view_team_reports'],
            'viewer': ['view_projects', 'view_reports']
        }

        user_permissions = role_permissions.get(self.role, [])

        if 'all' in user_permissions or permission in user_permissions:
            return True

        # Check custom permissions
        return self.permissions.get(permission, False)

    def activate(self):
        """Activate the membership."""
        self.is_active = True
        self.joined_at = timezone.now()
        self.save()

    def deactivate(self):
        """Deactivate the membership."""
        self.is_active = False
        self.save()


class WorkspaceMembership(models.Model):
    """
    WorkspaceMembership model for workspace-level permissions.

    Represents a user's membership in a workspace.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text=_('Workspace')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
        help_text=_('User')
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memberships',
        help_text=_('Team within the workspace')
    )

    # Permissions
    role = models.CharField(
        _('role'),
        max_length=20,
        default='member',
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
            ('viewer', 'Viewer'),
        ],
        help_text=_('User role in the workspace')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the membership is active')
    )

    # Permissions
    permissions = models.JSONField(
        _('permissions'),
        default=dict,
        blank=True,
        help_text=_('Custom permissions for this membership')
    )

    # Metadata
    joined_at = models.DateTimeField(
        _('joined at'),
        default=timezone.now,
        help_text=_('When the user joined the workspace')
    )

    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_workspace_members',
        help_text=_('User who added this member')
    )

    class Meta:
        ordering = ['-joined_at']
        verbose_name = _('workspace membership')
        verbose_name_plural = _('workspace memberships')
        unique_together = ['workspace', 'user']
        indexes = [
            models.Index(fields=['workspace', 'user']),
            models.Index(fields=['workspace', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['joined_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.workspace.name} ({self.role})"

    def has_permission(self, permission):
        """Check if membership has a specific permission."""
        # Check role-based permissions
        role_permissions = {
            'owner': ['all'],
            'admin': ['manage_team', 'manage_projects', 'view_reports'],
            'member': ['create_tasks', 'manage_own_tasks', 'view_team_reports'],
            'viewer': ['view_projects', 'view_reports']
        }

        user_permissions = role_permissions.get(self.role, [])

        if 'all' in user_permissions or permission in user_permissions:
            return True

        # Check custom permissions
        return self.permissions.get(permission, False)


class TeamMembership(models.Model):
    """
    TeamMembership model for team-level permissions.

    Represents a user's membership in a team.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text=_('Team')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='team_memberships',
        help_text=_('User')
    )

    # Permissions
    role = models.CharField(
        _('role'),
        max_length=20,
        default='member',
        choices=[
            ('lead', 'Team Lead'),
            ('member', 'Member'),
            ('viewer', 'Viewer'),
        ],
        help_text=_('User role in the team')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the membership is active')
    )

    # Metadata
    joined_at = models.DateTimeField(
        _('joined at'),
        default=timezone.now,
        help_text=_('When the user joined the team')
    )

    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_team_members',
        help_text=_('User who added this member')
    )

    class Meta:
        ordering = ['-joined_at']
        verbose_name = _('team membership')
        verbose_name_plural = _('team memberships')
        unique_together = ['team', 'user']
        indexes = [
            models.Index(fields=['team', 'user']),
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['joined_at']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team.name} ({self.role})"


class OrganizationInvitation(models.Model):
    """
    OrganizationInvitation model for managing organization invitations.

    Represents an invitation to join an organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text=_('Organization being invited to')
    )

    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_organization_invitations',
        help_text=_('User who sent the invitation')
    )

    # Invitation details
    email = models.EmailField(
        _('email'),
        help_text=_('Email address of the invited user')
    )

    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=True,
        help_text=_('First name of the invited user')
    )

    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=True,
        help_text=_('Last name of the invited user')
    )

    role = models.CharField(
        _('role'),
        max_length=20,
        default='member',
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
            ('viewer', 'Viewer'),
        ],
        help_text=_('Proposed role for the invited user')
    )

    # Invitation token
    token = models.CharField(
        _('token'),
        max_length=100,
        unique=True,
        help_text=_('Unique token for the invitation')
    )

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
            ('expired', 'Expired'),
        ],
        help_text=_('Invitation status')
    )

    # Workspaces to add to
    workspaces = models.ManyToManyField(
        Workspace,
        blank=True,
        related_name='invitations',
        help_text=_('Workspaces to add the user to')
    )

    # Message
    message = models.TextField(
        _('message'),
        blank=True,
        help_text=_('Personal message from the inviter')
    )

    # Timestamps
    sent_at = models.DateTimeField(
        _('sent at'),
        default=timezone.now,
        help_text=_('When the invitation was sent')
    )

    responded_at = models.DateTimeField(
        _('responded at'),
        null=True,
        blank=True,
        help_text=_('When the invitation was responded to')
    )

    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('When the invitation expires')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = _('organization invitation')
        verbose_name_plural = _('organization invitations')
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"Invitation to {self.organization.name} for {self.email}"

    def save(self, *args, **kwargs):
        """Save invitation and set expiration."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)

        if not self.token:
            self.token = str(uuid.uuid4())

        super().save(*args, **kwargs)

    def accept(self, user):
        """Accept the invitation."""
        if self.status == 'pending' and not self.is_expired():
            self.status = 'accepted'
            self.responded_at = timezone.now()

            # Create organization membership
            membership, created = OrganizationMembership.objects.get_or_create(
                organization=self.organization,
                user=user,
                defaults={
                    'role': self.role,
                    'invited_by': self.invited_by
                }
            )

            # Add to specified workspaces
            for workspace in self.workspaces.all():
                WorkspaceMembership.objects.get_or_create(
                    workspace=workspace,
                    user=user,
                    defaults={
                        'role': self.role,
                        'added_by': self.invited_by
                    }
                )

            self.save()
            return membership

    def decline(self):
        """Decline the invitation."""
        if self.status == 'pending':
            self.status = 'declined'
            self.responded_at = timezone.now()
            self.save()

    def is_expired(self):
        """Check if invitation is expired."""
        return timezone.now() > self.expires_at

    def expire(self):
        """Mark invitation as expired."""
        if self.status == 'pending':
            self.status = 'expired'
            self.save()


# Add reverse relationships
Organization.add_to_class(
    'users',
    models.ManyToManyField(
        'accounts.User',
        through=OrganizationMembership,
        related_name='organizations',
        help_text=_('Users in this organization')
    )
)

Workspace.add_to_class(
    'users',
    models.ManyToManyField(
        'accounts.User',
        through=WorkspaceMembership,
        related_name='workspaces',
        help_text=_('Users in this workspace')
    )
)

Team.add_to_class(
    'users',
    models.ManyToManyField(
        'accounts.User',
        through=TeamMembership,
        related_name='teams',
        help_text=_('Users in this team')
    )
)