"""
Tests for organizations app.

This module contains comprehensive tests for the organizations app,
including model tests, serializer tests, and view tests.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.core.exceptions import ValidationError

from .models import (
    Organization, Workspace, Team, OrganizationMembership,
    WorkspaceMembership, TeamMembership, OrganizationInvitation
)
from .serializers import (
    OrganizationSerializer, OrganizationCreateSerializer, WorkspaceSerializer,
    WorkspaceCreateSerializer, TeamSerializer, TeamCreateSerializer,
    OrganizationMembershipSerializer, WorkspaceMembershipSerializer,
    TeamMembershipSerializer, OrganizationInvitationSerializer,
    OrganizationInvitationCreateSerializer
)

User = get_user_model()


class OrganizationModelTest(TestCase):
    """Test Organization model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            description='A test organization',
            created_by=self.user,
            owner=self.user
        )

    def test_organization_creation(self):
        """Test organization creation."""
        self.assertEqual(self.organization.name, 'Test Organization')
        self.assertEqual(self.organization.slug, 'test-org')
        self.assertEqual(self.organization.description, 'A test organization')
        self.assertEqual(self.organization.created_by, self.user)
        self.assertEqual(self.organization.owner, self.user)
        self.assertTrue(self.organization.is_active)
        self.assertFalse(self.organization.is_verified)
        self.assertEqual(self.organization.subscription_plan, 'free')

    def test_organization_str(self):
        """Test organization string representation."""
        self.assertEqual(str(self.organization), 'Test Organization')

    def test_organization_save_sets_owner(self):
        """Test that save sets owner if not set."""
        org = Organization.objects.create(
            name='Test Org 2',
            slug='test-org-2',
            created_by=self.user
        )
        self.assertEqual(org.owner, self.user)

    def test_organization_members_count(self):
        """Test organization members count."""
        # Initially no members
        self.assertEqual(self.organization.get_members_count(), 0)

        # Add a member
        membership, created = self.organization.add_member(self.user, 'member')
        self.assertTrue(created)
        self.assertEqual(self.organization.get_members_count(), 1)

    def test_organization_add_member(self):
        """Test adding member to organization."""
        membership, created = self.organization.add_member(self.user, 'admin')
        self.assertTrue(created)
        self.assertEqual(membership.role, 'admin')
        self.assertTrue(membership.is_active)

        # Try to add the same user again
        membership2, created2 = self.organization.add_member(self.user, 'member')
        self.assertFalse(created2)
        self.assertEqual(membership, membership2)

    def test_organization_remove_member(self):
        """Test removing member from organization."""
        # Add member first
        self.organization.add_member(self.user, 'member')

        # Remove member
        removed = self.organization.remove_member(self.user)
        self.assertTrue(removed)
        self.assertEqual(self.organization.get_members_count(), 0)

        # Try to remove non-member
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        removed = self.organization.remove_member(other_user)
        self.assertFalse(removed)

    def test_organization_feature_management(self):
        """Test organization feature management."""
        # Enable feature
        self.organization.enable_feature('ai_assistant', {'enabled': True})
        self.assertTrue(self.organization.has_feature('ai_assistant'))
        self.assertEqual(self.organization.features_enabled['ai_assistant'], {'enabled': True})

        # Disable feature
        self.organization.disable_feature('ai_assistant')
        self.assertFalse(self.organization.has_feature('ai_assistant'))
        self.assertNotIn('ai_assistant', self.organization.features_enabled)

    def test_organization_subscription_limits(self):
        """Test organization subscription limits."""
        limits = self.organization.get_subscription_limits()

        expected_limits = {
            'max_users': 3,
            'max_projects': 2,
            'max_storage_gb': 1,
            'features': ['basic_time_tracking', 'basic_reporting']
        }

        self.assertEqual(limits, expected_limits)

    def test_organization_within_limits(self):
        """Test organization within limits check."""
        # Should be within limits initially
        self.assertTrue(self.organization.is_within_limits('users', 1))
        self.assertTrue(self.organization.is_within_limits('projects', 1))

        # Should exceed limits
        self.assertFalse(self.organization.is_within_limits('users', 5))
        self.assertFalse(self.organization.is_within_limits('projects', 3))


class WorkspaceModelTest(TestCase):
    """Test Workspace model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            description='A test workspace',
            organization=self.organization,
            created_by=self.user
        )

    def test_workspace_creation(self):
        """Test workspace creation."""
        self.assertEqual(self.workspace.name, 'Test Workspace')
        self.assertEqual(self.workspace.slug, 'test-workspace')
        self.assertEqual(self.workspace.description, 'A test workspace')
        self.assertEqual(self.workspace.organization, self.organization)
        self.assertEqual(self.workspace.created_by, self.user)
        self.assertTrue(self.workspace.is_active)
        self.assertFalse(self.workspace.is_private)

    def test_workspace_str(self):
        """Test workspace string representation."""
        expected = 'Test Organization: Test Workspace'
        self.assertEqual(str(self.workspace), expected)

    def test_workspace_save_inherits_settings(self):
        """Test that workspace inherits organization settings."""
        self.organization.timezone = 'America/New_York'
        self.organization.currency = 'USD'
        self.organization.save()

        workspace = Workspace.objects.create(
            name='Test Workspace 2',
            slug='test-workspace-2',
            organization=self.organization,
            created_by=self.user
        )

        self.assertEqual(workspace.timezone, 'America/New_York')
        self.assertEqual(workspace.currency, 'USD')

    def test_workspace_members_count(self):
        """Test workspace members count."""
        # Initially no members
        self.assertEqual(self.workspace.get_members_count(), 0)

        # Add a member
        membership, created = self.workspace.add_member(self.user, 'member')
        self.assertTrue(created)
        self.assertEqual(self.workspace.get_members_count(), 1)

    def test_workspace_add_member(self):
        """Test adding member to workspace."""
        membership, created = self.workspace.add_member(self.user, 'admin')
        self.assertTrue(created)
        self.assertEqual(membership.role, 'admin')
        self.assertTrue(membership.is_active)

    def test_workspace_remove_member(self):
        """Test removing member from workspace."""
        # Add member first
        self.workspace.add_member(self.user, 'member')

        # Remove member
        self.workspace.remove_member(self.user)
        self.assertEqual(self.workspace.get_members_count(), 0)

    def test_workspace_user_access(self):
        """Test workspace user access."""
        # Private workspace
        self.workspace.is_private = True
        self.workspace.save()

        # Non-member should not have access
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.assertFalse(self.workspace.can_user_access(other_user))

        # Member should have access
        self.workspace.add_member(other_user, 'member')
        self.assertTrue(self.workspace.can_user_access(other_user))

        # Public workspace
        self.workspace.is_private = False
        self.workspace.save()

        # Organization member should have access
        org_member = User.objects.create_user(
            email='orgmember@example.com',
            password='testpass123'
        )
        self.organization.add_member(org_member, 'member')
        self.assertTrue(self.workspace.can_user_access(org_member))

    def test_workspace_user_role(self):
        """Test workspace user role."""
        # Add member with specific role
        self.workspace.add_member(self.user, 'admin')
        role = self.workspace.get_user_role(self.user)
        self.assertEqual(role, 'admin')

        # Non-member should have no role
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        role = self.workspace.get_user_role(other_user)
        self.assertIsNone(role)


class TeamModelTest(TestCase):
    """Test Team model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            organization=self.organization,
            created_by=self.user
        )
        self.team = Team.objects.create(
            name='Test Team',
            slug='test-team',
            description='A test team',
            workspace=self.workspace,
            lead=self.user,
            created_by=self.user
        )

    def test_team_creation(self):
        """Test team creation."""
        self.assertEqual(self.team.name, 'Test Team')
        self.assertEqual(self.team.slug, 'test-team')
        self.assertEqual(self.team.description, 'A test team')
        self.assertEqual(self.team.workspace, self.workspace)
        self.assertEqual(self.team.lead, self.user)
        self.assertEqual(self.team.created_by, self.user)
        self.assertTrue(self.team.is_active)

    def test_team_str(self):
        """Test team string representation."""
        expected = 'Test Workspace: Test Team'
        self.assertEqual(str(self.team), expected)

    def test_team_members_count(self):
        """Test team members count."""
        # Initially no members
        self.assertEqual(self.team.get_members_count(), 0)

        # Add a member
        membership, created = self.team.add_member(self.user, 'member')
        self.assertTrue(created)
        self.assertEqual(self.team.get_members_count(), 1)

    def test_team_add_member(self):
        """Test adding member to team."""
        membership, created = self.team.add_member(self.user, 'lead')
        self.assertTrue(created)
        self.assertEqual(membership.role, 'lead')
        self.assertTrue(membership.is_active)

    def test_team_remove_member(self):
        """Test removing member from team."""
        # Add member first
        self.team.add_member(self.user, 'member')

        # Remove member
        self.team.remove_member(self.user)
        self.assertEqual(self.team.get_members_count(), 0)


class OrganizationMembershipModelTest(TestCase):
    """Test OrganizationMembership model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role='admin',
            invited_by=self.user
        )

    def test_membership_creation(self):
        """Test membership creation."""
        self.assertEqual(self.membership.organization, self.organization)
        self.assertEqual(self.membership.user, self.user)
        self.assertEqual(self.membership.role, 'admin')
        self.assertEqual(self.membership.invited_by, self.user)
        self.assertTrue(self.membership.is_active)
        self.assertIsNotNone(self.membership.invited_at)
        self.assertIsNotNone(self.membership.joined_at)

    def test_membership_str(self):
        """Test membership string representation."""
        expected = 'Test User: Test Organization (admin)'
        self.assertEqual(str(self.membership), expected)

    def test_membership_save_sets_joined_at(self):
        """Test that save sets joined_at when activated."""
        membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role='member',
            invited_by=self.user,
            is_active=False
        )

        # Initially no joined_at
        self.assertIsNone(membership.joined_at)

        # Activate
        membership.activate()
        self.assertIsNotNone(membership.joined_at)
        self.assertTrue(membership.is_active)

    def test_membership_has_permission(self):
        """Test membership permission checking."""
        # Owner should have all permissions
        self.membership.role = 'owner'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('manage_users'))
        self.assertTrue(self.membership.has_permission('all'))

        # Admin should have specific permissions
        self.membership.role = 'admin'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('manage_users'))
        self.assertFalse(self.membership.has_permission('nonexistent'))

        # Member should have basic permissions
        self.membership.role = 'member'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('create_projects'))
        self.assertFalse(self.membership.has_permission('manage_users'))

        # Viewer should have limited permissions
        self.membership.role = 'viewer'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('view_projects'))
        self.assertFalse(self.membership.has_permission('create_projects'))

    def test_membership_activate_deactivate(self):
        """Test membership activation and deactivation."""
        # Deactivate
        self.membership.deactivate()
        self.assertFalse(self.membership.is_active)

        # Activate
        self.membership.activate()
        self.assertTrue(self.membership.is_active)


class WorkspaceMembershipModelTest(TestCase):
    """Test WorkspaceMembership model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            organization=self.organization,
            created_by=self.user
        )
        self.membership = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.user,
            role='admin',
            added_by=self.user
        )

    def test_membership_creation(self):
        """Test membership creation."""
        self.assertEqual(self.membership.workspace, self.workspace)
        self.assertEqual(self.membership.user, self.user)
        self.assertEqual(self.membership.role, 'admin')
        self.assertEqual(self.membership.added_by, self.user)
        self.assertTrue(self.membership.is_active)
        self.assertIsNotNone(self.membership.joined_at)

    def test_membership_str(self):
        """Test membership string representation."""
        expected = 'Test User: Test Workspace (admin)'
        self.assertEqual(str(self.membership), expected)

    def test_membership_has_permission(self):
        """Test membership permission checking."""
        # Owner should have all permissions
        self.membership.role = 'owner'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('manage_team'))
        self.assertTrue(self.membership.has_permission('all'))

        # Admin should have specific permissions
        self.membership.role = 'admin'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('manage_team'))
        self.assertFalse(self.membership.has_permission('nonexistent'))

        # Member should have basic permissions
        self.membership.role = 'member'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('create_tasks'))
        self.assertFalse(self.membership.has_permission('manage_team'))

        # Viewer should have limited permissions
        self.membership.role = 'viewer'
        self.membership.save()
        self.assertTrue(self.membership.has_permission('view_projects'))
        self.assertFalse(self.membership.has_permission('create_tasks'))


class TeamMembershipModelTest(TestCase):
    """Test TeamMembership model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            organization=self.organization,
            created_by=self.user
        )
        self.team = Team.objects.create(
            name='Test Team',
            slug='test-team',
            workspace=self.workspace,
            created_by=self.user
        )
        self.membership = TeamMembership.objects.create(
            team=self.team,
            user=self.user,
            role='lead',
            added_by=self.user
        )

    def test_membership_creation(self):
        """Test membership creation."""
        self.assertEqual(self.membership.team, self.team)
        self.assertEqual(self.membership.user, self.user)
        self.assertEqual(self.membership.role, 'lead')
        self.assertEqual(self.membership.added_by, self.user)
        self.assertTrue(self.membership.is_active)
        self.assertIsNotNone(self.membership.joined_at)

    def test_membership_str(self):
        """Test membership string representation."""
        expected = 'Test User: Test Team (lead)'
        self.assertEqual(str(self.membership), expected)


class OrganizationInvitationModelTest(TestCase):
    """Test OrganizationInvitation model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.invited_user = User.objects.create_user(
            email='invited@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            invited_by=self.user,
            email='invited@example.com',
            first_name='Invited',
            last_name='User',
            role='member'
        )

    def test_invitation_creation(self):
        """Test invitation creation."""
        self.assertEqual(self.invitation.organization, self.organization)
        self.assertEqual(self.invitation.invited_by, self.user)
        self.assertEqual(self.invitation.email, 'invited@example.com')
        self.assertEqual(self.invitation.first_name, 'Invited')
        self.assertEqual(self.invitation.last_name, 'User')
        self.assertEqual(self.invitation.role, 'member')
        self.assertEqual(self.invitation.status, 'pending')
        self.assertIsNotNone(self.invitation.token)
        self.assertIsNotNone(self.invitation.sent_at)
        self.assertIsNotNone(self.invitation.expires_at)

    def test_invitation_str(self):
        """Test invitation string representation."""
        expected = "Invitation to Test Organization for invited@example.com"
        self.assertEqual(str(self.invitation), expected)

    def test_invitation_save_sets_expiration(self):
        """Test that save sets expiration date."""
        invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            invited_by=self.user,
            email='test2@example.com',
            role='member'
        )
        self.assertIsNotNone(invitation.expires_at)

    def test_invitation_accept(self):
        """Test invitation acceptance."""
        membership = self.invitation.accept(self.invited_user)

        self.assertIsNotNone(membership)
        self.assertEqual(membership.organization, self.organization)
        self.assertEqual(membership.user, self.invited_user)
        self.assertEqual(membership.role, 'member')
        self.assertEqual(self.invitation.status, 'accepted')
        self.assertIsNotNone(self.invitation.responded_at)

    def test_invitation_decline(self):
        """Test invitation decline."""
        self.invitation.decline()

        self.assertEqual(self.invitation.status, 'declined')
        self.assertIsNotNone(self.invitation.responded_at)

    def test_invitation_is_expired(self):
        """Test invitation expiration check."""
        # Not expired
        self.assertFalse(self.invitation.is_expired())

        # Expired
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        self.assertTrue(self.invitation.is_expired())

    def test_invitation_expire(self):
        """Test invitation expiration."""
        self.invitation.expire()
        self.assertEqual(self.invitation.status, 'expired')


# Pytest-style tests
@pytest.mark.django_db
def test_organization_serializer():
    """Test OrganizationSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    serializer = OrganizationSerializer(organization)
    data = serializer.data

    assert data['name'] == 'Test Organization'
    assert data['slug'] == 'test-org'
    assert data['is_active'] is True
    assert data['subscription_plan'] == 'free'
    assert data['members_count'] == 0
    assert data['workspaces_count'] == 0


@pytest.mark.django_db
def test_workspace_serializer():
    """Test WorkspaceSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )

    serializer = WorkspaceSerializer(workspace)
    data = serializer.data

    assert data['name'] == 'Test Workspace'
    assert data['slug'] == 'test-workspace'
    assert data['organization_name'] == 'Test Organization'
    assert data['is_active'] is True
    assert data['members_count'] == 0


@pytest.mark.django_db
def test_team_serializer():
    """Test TeamSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )
    team = Team.objects.create(
        name='Test Team',
        slug='test-team',
        workspace=workspace,
        created_by=user
    )

    serializer = TeamSerializer(team)
    data = serializer.data

    assert data['name'] == 'Test Team'
    assert data['slug'] == 'test-team'
    assert data['workspace_name'] == 'Test Workspace'
    assert data['is_active'] is True
    assert data['members_count'] == 0


@pytest.mark.django_db
def test_organization_membership_serializer():
    """Test OrganizationMembershipSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role='admin',
        invited_by=user
    )

    serializer = OrganizationMembershipSerializer(membership)
    data = serializer.data

    assert data['role'] == 'admin'
    assert data['is_active'] is True
    assert data['user_name'] == 'Test User'


@pytest.mark.django_db
def test_workspace_membership_serializer():
    """Test WorkspaceMembershipSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )
    membership = WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role='admin',
        added_by=user
    )

    serializer = WorkspaceMembershipSerializer(membership)
    data = serializer.data

    assert data['role'] == 'admin'
    assert data['is_active'] is True
    assert data['user_name'] == 'Test User'


@pytest.mark.django_db
def test_team_membership_serializer():
    """Test TeamMembershipSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )
    team = Team.objects.create(
        name='Test Team',
        slug='test-team',
        workspace=workspace,
        created_by=user
    )
    membership = TeamMembership.objects.create(
        team=team,
        user=user,
        role='lead',
        added_by=user
    )

    serializer = TeamMembershipSerializer(membership)
    data = serializer.data

    assert data['role'] == 'lead'
    assert data['is_active'] is True
    assert data['user_name'] == 'Test User'


@pytest.mark.django_db
def test_organization_invitation_serializer():
    """Test OrganizationInvitationSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        invited_by=user,
        email='invited@example.com',
        role='member'
    )

    serializer = OrganizationInvitationSerializer(invitation)
    data = serializer.data

    assert data['email'] == 'invited@example.com'
    assert data['role'] == 'member'
    assert data['status'] == 'pending'
    assert data['is_expired'] is False


@pytest.mark.django_db
def test_organization_workflow():
    """Test complete organization workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Create organization
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    assert organization.name == 'Test Organization'
    assert organization.owner == user
    assert organization.get_members_count() == 0

    # Create workspace
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )

    assert workspace.name == 'Test Workspace'
    assert workspace.organization == organization
    assert workspace.get_members_count() == 0

    # Create team
    team = Team.objects.create(
        name='Test Team',
        slug='test-team',
        workspace=workspace,
        created_by=user
    )

    assert team.name == 'Test Team'
    assert team.workspace == workspace
    assert team.get_members_count() == 0

    # Add member to organization
    membership, created = organization.add_member(user, 'admin')
    assert created
    assert membership.role == 'admin'
    assert organization.get_members_count() == 1

    # Add member to workspace
    workspace_membership, created = workspace.add_member(user, 'admin')
    assert created
    assert workspace_membership.role == 'admin'
    assert workspace.get_members_count() == 1

    # Add member to team
    team_membership, created = team.add_member(user, 'lead')
    assert created
    assert team_membership.role == 'lead'
    assert team.get_members_count() == 1


@pytest.mark.django_db
def test_invitation_workflow():
    """Test complete invitation workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    invited_user = User.objects.create_user(
        email='invited@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    # Create invitation
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        invited_by=user,
        email='invited@example.com',
        role='member'
    )

    assert invitation.status == 'pending'
    assert not invitation.is_expired()

    # Accept invitation
    membership = invitation.accept(invited_user)

    assert membership is not None
    assert membership.organization == organization
    assert membership.user == invited_user
    assert membership.role == 'member'
    assert invitation.status == 'accepted'

    # Check membership was created
    org_membership = OrganizationMembership.objects.get(
        organization=organization,
        user=invited_user
    )
    assert org_membership.role == 'member'
    assert org_membership.is_active


@pytest.mark.django_db
def test_permission_system():
    """Test permission system."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        organization=organization,
        created_by=user
    )

    # Test organization permissions
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role='admin',
        invited_by=user
    )

    assert membership.has_permission('manage_users')
    assert membership.has_permission('manage_workspaces')
    assert not membership.has_permission('nonexistent')

    # Test workspace permissions
    workspace_membership = WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role='admin',
        added_by=user
    )

    assert workspace_membership.has_permission('manage_team')
    assert workspace_membership.has_permission('manage_projects')
    assert not workspace_membership.has_permission('nonexistent')


@pytest.mark.django_db
def test_hierarchy_integrity():
    """Test organization hierarchy integrity."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Create organization
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    # Create workspaces
    workspace1 = Workspace.objects.create(
        name='Workspace 1',
        slug='workspace-1',
        organization=organization,
        created_by=user
    )
    workspace2 = Workspace.objects.create(
        name='Workspace 2',
        slug='workspace-2',
        organization=organization,
        created_by=user
    )

    # Create teams
    team1 = Team.objects.create(
        name='Team 1',
        slug='team-1',
        workspace=workspace1,
        created_by=user
    )
    team2 = Team.objects.create(
        name='Team 2',
        slug='team-2',
        workspace=workspace2,
        created_by=user
    )

    # Verify hierarchy
    assert organization.workspaces.count() == 2
    assert workspace1.teams.count() == 1
    assert workspace2.teams.count() == 1
    assert team1.workspace == workspace1
    assert team2.workspace == workspace2

    # Test cascading deletes
    workspace1.delete()
    assert Team.objects.filter(workspace=workspace1).count() == 0
    assert organization.workspaces.count() == 1

    organization.delete()
    assert Workspace.objects.filter(organization=organization).count() == 0
    assert Team.objects.filter(workspace__organization=organization).count() == 0