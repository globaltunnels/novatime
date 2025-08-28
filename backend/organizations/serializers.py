"""
Serializers for organizations app.

This module contains serializers for Organization, Workspace, Team,
OrganizationMembership, WorkspaceMembership, TeamMembership,
and OrganizationInvitation models for API serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    Organization, Workspace, Team, OrganizationMembership,
    WorkspaceMembership, TeamMembership, OrganizationInvitation
)

User = get_user_model()


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    invited_by_name = serializers.CharField(
        source='invited_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = OrganizationMembership
        fields = [
            'id', 'organization', 'user', 'user_name', 'user_email', 'role',
            'is_active', 'permissions', 'invited_at', 'joined_at',
            'invited_by', 'invited_by_name'
        ]
        read_only_fields = ['id', 'invited_at', 'joined_at']

    def validate_role(self, value):
        """Validate role permissions."""
        request = self.context.get('request')
        if request and request.user:
            # Check if user has permission to assign this role
            membership = OrganizationMembership.objects.filter(
                organization=self.instance.organization if self.instance else self.context.get('organization'),
                user=request.user,
                is_active=True
            ).first()

            if membership and membership.role not in ['owner', 'admin']:
                if value in ['owner', 'admin']:
                    raise serializers.ValidationError(
                        _("You don't have permission to assign this role.")
                    )

        return value


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    """Serializer for WorkspaceMembership model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    team_name = serializers.CharField(
        source='team.name',
        read_only=True
    )
    added_by_name = serializers.CharField(
        source='added_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = WorkspaceMembership
        fields = [
            'id', 'workspace', 'user', 'user_name', 'user_email', 'team',
            'team_name', 'role', 'is_active', 'permissions', 'joined_at',
            'added_by', 'added_by_name'
        ]
        read_only_fields = ['id', 'joined_at']


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TeamMembership model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    added_by_name = serializers.CharField(
        source='added_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = TeamMembership
        fields = [
            'id', 'team', 'user', 'user_name', 'user_email', 'role',
            'is_active', 'joined_at', 'added_by', 'added_by_name'
        ]
        read_only_fields = ['id', 'joined_at']


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""

    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )
    lead_name = serializers.CharField(
        source='lead.get_full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'slug', 'description', 'workspace', 'workspace_name',
            'lead', 'lead_name', 'color', 'is_active', 'created_by',
            'created_by_name', 'members_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'members_count', 'created_at', 'updated_at']

    def get_members_count(self, obj):
        """Get members count."""
        return obj.get_members_count()


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for Workspace model."""

    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    members_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    teams_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'slug', 'description', 'organization', 'organization_name',
            'timezone', 'currency', 'is_active', 'is_private', 'created_by',
            'created_by_name', 'members_count', 'projects_count', 'tasks_count',
            'teams_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'members_count', 'projects_count', 'tasks_count', 'teams_count',
            'created_at', 'updated_at'
        ]

    def get_members_count(self, obj):
        """Get members count."""
        return obj.get_members_count()

    def get_projects_count(self, obj):
        """Get projects count."""
        return obj.get_projects_count()

    def get_tasks_count(self, obj):
        """Get tasks count."""
        return obj.get_tasks_count()

    def get_teams_count(self, obj):
        """Get teams count."""
        return obj.teams.count()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    owner_name = serializers.CharField(
        source='owner.get_full_name',
        read_only=True
    )
    members_count = serializers.SerializerMethodField()
    active_users_count = serializers.SerializerMethodField()
    workspaces_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    subscription_limits = serializers.SerializerMethodField()
    storage_usage_gb = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'website', 'email', 'phone',
            'address_line_1', 'address_line_2', 'city', 'state_province',
            'postal_code', 'country', 'industry', 'company_size', 'logo_url',
            'primary_color', 'secondary_color', 'timezone', 'date_format',
            'currency', 'language', 'subscription_plan', 'subscription_status',
            'trial_end_date', 'max_users', 'max_projects', 'max_storage_gb',
            'features_enabled', 'is_active', 'is_verified', 'created_by',
            'created_by_name', 'owner', 'owner_name', 'members_count',
            'active_users_count', 'workspaces_count', 'projects_count',
            'subscription_limits', 'storage_usage_gb', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'members_count', 'active_users_count', 'workspaces_count',
            'projects_count', 'subscription_limits', 'storage_usage_gb',
            'created_at', 'updated_at'
        ]

    def get_members_count(self, obj):
        """Get members count."""
        return obj.get_members_count()

    def get_active_users_count(self, obj):
        """Get active users count."""
        return obj.get_active_users_count()

    def get_workspaces_count(self, obj):
        """Get workspaces count."""
        return obj.get_workspaces_count()

    def get_projects_count(self, obj):
        """Get projects count."""
        return obj.get_projects_count()

    def get_subscription_limits(self, obj):
        """Get subscription limits."""
        return obj.get_subscription_limits()

    def get_storage_usage_gb(self, obj):
        """Get storage usage."""
        return obj.get_storage_usage_gb()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations."""

    class Meta:
        model = Organization
        fields = [
            'name', 'slug', 'description', 'website', 'email', 'phone',
            'address_line_1', 'address_line_2', 'city', 'state_province',
            'postal_code', 'country', 'industry', 'company_size', 'timezone',
            'date_format', 'currency', 'language'
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness."""
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                _("An organization with this slug already exists.")
            )
        return value

    def create(self, validated_data):
        """Create organization."""
        validated_data['created_by'] = self.context['request'].user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workspaces."""

    class Meta:
        model = Workspace
        fields = [
            'name', 'slug', 'description', 'timezone', 'currency', 'is_private'
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness within organization."""
        organization = self.context.get('organization')
        if organization and Workspace.objects.filter(
            organization=organization, slug=value
        ).exists():
            raise serializers.ValidationError(
                _("A workspace with this slug already exists in this organization.")
            )
        return value

    def create(self, validated_data):
        """Create workspace."""
        validated_data['organization'] = self.context['organization']
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teams."""

    class Meta:
        model = Team
        fields = [
            'name', 'slug', 'description', 'lead', 'color'
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness within workspace."""
        workspace = self.context.get('workspace')
        if workspace and Team.objects.filter(
            workspace=workspace, slug=value
        ).exists():
            raise serializers.ValidationError(
                _("A team with this slug already exists in this workspace.")
            )
        return value

    def create(self, validated_data):
        """Create team."""
        validated_data['workspace'] = self.context['workspace']
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationInvitation model."""

    invited_by_name = serializers.CharField(
        source='invited_by.get_full_name',
        read_only=True
    )
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    workspaces_data = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'organization', 'organization_name', 'invited_by',
            'invited_by_name', 'email', 'first_name', 'last_name', 'role',
            'token', 'status', 'workspaces', 'workspaces_data', 'message',
            'sent_at', 'responded_at', 'expires_at', 'is_expired', 'created_at'
        ]
        read_only_fields = [
            'id', 'token', 'sent_at', 'responded_at', 'is_expired', 'created_at'
        ]

    def get_workspaces_data(self, obj):
        """Get workspaces data."""
        workspaces = obj.workspaces.all()
        return WorkspaceSerializer(workspaces, many=True, context=self.context).data

    def get_is_expired(self, obj):
        """Check if invitation is expired."""
        return obj.is_expired()


class OrganizationInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organization invitations."""

    class Meta:
        model = OrganizationInvitation
        fields = [
            'email', 'first_name', 'last_name', 'role', 'workspaces', 'message'
        ]

    def validate_email(self, value):
        """Validate email uniqueness for organization."""
        organization = self.context.get('organization')
        if organization:
            # Check if user is already a member
            if OrganizationMembership.objects.filter(
                organization=organization,
                user__email=value,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is already a member of the organization.")
                )

            # Check if invitation already exists
            if OrganizationInvitation.objects.filter(
                organization=organization,
                email=value,
                status='pending'
            ).exists():
                raise serializers.ValidationError(
                    _("An invitation has already been sent to this email.")
                )

        return value

    def validate_workspaces(self, value):
        """Validate workspaces belong to organization."""
        organization = self.context.get('organization')
        if organization:
            for workspace in value:
                if workspace.organization != organization:
                    raise serializers.ValidationError(
                        _("Workspace does not belong to this organization.")
                    )
        return value

    def create(self, validated_data):
        """Create invitation."""
        validated_data['organization'] = self.context['organization']
        validated_data['invited_by'] = self.context['request'].user
        return super().create(validated_data)


class OrganizationStatsSerializer(serializers.Serializer):
    """Serializer for organization statistics."""

    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    total_workspaces = serializers.IntegerField()
    active_workspaces = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    total_time_entries = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    storage_usage_gb = serializers.DecimalField(max_digits=8, decimal_places=2)
    subscription_usage = serializers.DictField()
    member_growth = serializers.ListField()
    workspace_growth = serializers.ListField()
    project_growth = serializers.ListField()


class WorkspaceStatsSerializer(serializers.Serializer):
    """Serializer for workspace statistics."""

    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    total_teams = serializers.IntegerField()
    active_teams = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    total_time_entries = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    member_growth = serializers.ListField()
    project_growth = serializers.ListField()
    task_completion_trend = serializers.ListField()


class TeamStatsSerializer(serializers.Serializer):
    """Serializer for team statistics."""

    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    total_time_entries = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    billable_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_hours_per_member = serializers.DecimalField(max_digits=6, decimal_places=2)
    task_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    productivity_trend = serializers.ListField()
    workload_distribution = serializers.ListField()


class OrganizationSettingsSerializer(serializers.Serializer):
    """Serializer for organization settings."""

    # Basic settings
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Address
    address_line_1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Branding
    logo_url = serializers.URLField(required=False, allow_blank=True)
    primary_color = serializers.CharField(max_length=7, required=False)
    secondary_color = serializers.CharField(max_length=7, required=False)

    # Preferences
    timezone = serializers.CharField(max_length=50, required=False)
    date_format = serializers.CharField(max_length=20, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    language = serializers.CharField(max_length=10, required=False)

    # Features
    features_enabled = serializers.DictField(required=False)


class WorkspaceSettingsSerializer(serializers.Serializer):
    """Serializer for workspace settings."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    is_private = serializers.BooleanField(required=False)


class TeamSettingsSerializer(serializers.Serializer):
    """Serializer for team settings."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    lead = serializers.UUIDField(required=False)
    color = serializers.CharField(max_length=7, required=False)


class OrganizationMemberAddSerializer(serializers.Serializer):
    """Serializer for adding organization members."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(
        choices=['owner', 'admin', 'member', 'viewer'],
        default='member'
    )
    workspaces = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    message = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Validate email."""
        if User.objects.filter(email=value).exists():
            user = User.objects.get(email=value)
            if OrganizationMembership.objects.filter(
                organization=self.context['organization'],
                user=user,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is already a member of the organization.")
                )
        return value

    def validate_workspaces(self, value):
        """Validate workspaces."""
        organization = self.context['organization']
        for workspace_id in value:
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                if workspace.organization != organization:
                    raise serializers.ValidationError(
                        _("Workspace does not belong to this organization.")
                    )
            except Workspace.DoesNotExist:
                raise serializers.ValidationError(
                    _("Invalid workspace ID.")
                )
        return value


class WorkspaceMemberAddSerializer(serializers.Serializer):
    """Serializer for adding workspace members."""

    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=['owner', 'admin', 'member', 'viewer'],
        default='member'
    )
    team_id = serializers.UUIDField(required=False)

    def validate_user_id(self, value):
        """Validate user."""
        try:
            user = User.objects.get(id=value)
            workspace = self.context['workspace']

            # Check if user is already a member
            if WorkspaceMembership.objects.filter(
                workspace=workspace,
                user=user,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is already a member of the workspace.")
                )

            # Check if user is a member of the organization
            if not OrganizationMembership.objects.filter(
                organization=workspace.organization,
                user=user,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is not a member of the organization.")
                )

        except User.DoesNotExist:
            raise serializers.ValidationError(_("Invalid user ID."))

        return value

    def validate_team_id(self, value):
        """Validate team."""
        if value:
            try:
                team = Team.objects.get(id=value)
                workspace = self.context['workspace']

                if team.workspace != workspace:
                    raise serializers.ValidationError(
                        _("Team does not belong to this workspace.")
                    )

            except Team.DoesNotExist:
                raise serializers.ValidationError(_("Invalid team ID."))

        return value


class TeamMemberAddSerializer(serializers.Serializer):
    """Serializer for adding team members."""

    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=['lead', 'member', 'viewer'],
        default='member'
    )

    def validate_user_id(self, value):
        """Validate user."""
        try:
            user = User.objects.get(id=value)
            team = self.context['team']

            # Check if user is already a member
            if TeamMembership.objects.filter(
                team=team,
                user=user,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is already a member of the team.")
                )

            # Check if user is a member of the workspace
            if not WorkspaceMembership.objects.filter(
                workspace=team.workspace,
                user=user,
                is_active=True
            ).exists():
                raise serializers.ValidationError(
                    _("This user is not a member of the workspace.")
                )

        except User.DoesNotExist:
            raise serializers.ValidationError(_("Invalid user ID."))

        return value


class OrganizationTransferSerializer(serializers.Serializer):
    """Serializer for transferring organization ownership."""

    new_owner_id = serializers.UUIDField()
    transfer_reason = serializers.CharField(required=False, allow_blank=True)

    def validate_new_owner_id(self, value):
        """Validate new owner."""
        try:
            user = User.objects.get(id=value)
            organization = self.context['organization']

            # Check if user is an active member
            membership = OrganizationMembership.objects.filter(
                organization=organization,
                user=user,
                is_active=True
            ).first()

            if not membership:
                raise serializers.ValidationError(
                    _("User is not an active member of the organization.")
                )

            # Check if user has appropriate role
            if membership.role not in ['owner', 'admin']:
                raise serializers.ValidationError(
                    _("User must be an owner or admin to take ownership.")
                )

        except User.DoesNotExist:
            raise serializers.ValidationError(_("Invalid user ID."))

        return value


class OrganizationBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk organization actions."""

    organization_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of organization IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'update_plan'],
        help_text=_('Action to perform on the organizations')
    )

    subscription_plan = serializers.ChoiceField(
        choices=['free', 'starter', 'professional', 'enterprise'],
        required=False,
        help_text=_('New subscription plan (for update_plan action)')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')

        if action == 'update_plan' and 'subscription_plan' not in data:
            raise serializers.ValidationError(
                _("Subscription plan is required for update_plan action.")
            )

        return data


class WorkspaceBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk workspace actions."""

    workspace_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of workspace IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'transfer'],
        help_text=_('Action to perform on the workspaces')
    )

    organization_id = serializers.UUIDField(
        required=False,
        help_text=_('Organization ID to transfer to (for transfer action)')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')

        if action == 'transfer' and 'organization_id' not in data:
            raise serializers.ValidationError(
                _("Organization ID is required for transfer action.")
            )

        return data


class OrganizationExportSerializer(serializers.Serializer):
    """Serializer for exporting organization data."""

    include_members = serializers.BooleanField(default=True)
    include_workspaces = serializers.BooleanField(default=True)
    include_projects = serializers.BooleanField(default=True)
    include_tasks = serializers.BooleanField(default=True)
    include_time_entries = serializers.BooleanField(default=True)
    include_attachments = serializers.BooleanField(default=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel'],
        default='json'
    )


class OrganizationImportSerializer(serializers.Serializer):
    """Serializer for importing organization data."""

    file = serializers.FileField()
    import_mode = serializers.ChoiceField(
        choices=['merge', 'replace', 'append'],
        default='merge'
    )
    include_members = serializers.BooleanField(default=True)
    include_workspaces = serializers.BooleanField(default=True)
    include_projects = serializers.BooleanField(default=True)
    include_tasks = serializers.BooleanField(default=True)
    include_time_entries = serializers.BooleanField(default=True)
    preview_only = serializers.BooleanField(default=False)