"""
Views for organizations app.

This module contains API views for managing organizations, workspaces,
teams, memberships, invitations, and related functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import (
    Organization, Workspace, Team, OrganizationMembership,
    WorkspaceMembership, TeamMembership, OrganizationInvitation
)
from .serializers import (
    OrganizationSerializer, OrganizationCreateSerializer, WorkspaceSerializer,
    WorkspaceCreateSerializer, TeamSerializer, TeamCreateSerializer,
    OrganizationMembershipSerializer, WorkspaceMembershipSerializer,
    TeamMembershipSerializer, OrganizationInvitationSerializer,
    OrganizationInvitationCreateSerializer, OrganizationStatsSerializer,
    WorkspaceStatsSerializer, TeamStatsSerializer, OrganizationSettingsSerializer,
    WorkspaceSettingsSerializer, TeamSettingsSerializer,
    OrganizationMemberAddSerializer, WorkspaceMemberAddSerializer,
    TeamMemberAddSerializer, OrganizationTransferSerializer,
    OrganizationBulkActionSerializer, WorkspaceBulkActionSerializer,
    OrganizationExportSerializer, OrganizationImportSerializer
)

User = get_user_model()


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization model."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter organizations by current user's access."""
        return Organization.objects.filter(
            Q(users=self.request.user) |
            Q(created_by=self.request.user) |
            Q(owner=self.request.user)
        ).distinct().prefetch_related('owner', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def perform_create(self, serializer):
        """Create organization."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get organization statistics."""
        organization = self.get_object()

        # Get basic counts
        total_members = organization.get_members_count()
        active_members = organization.get_active_users_count()
        total_workspaces = organization.get_workspaces_count()
        active_workspaces = organization.workspaces.filter(is_active=True).count()
        total_projects = organization.get_projects_count()
        active_projects = organization.workspaces.filter(
            projects__is_active=True
        ).distinct().count()

        # Get task and time entry stats (simplified)
        total_tasks = organization.workspaces.aggregate(
            total_tasks=Count('projects__tasks')
        )['total_tasks'] or 0

        completed_tasks = organization.workspaces.aggregate(
            completed_tasks=Count('projects__tasks', filter=Q(projects__tasks__status='done'))
        )['completed_tasks'] or 0

        # Time entries stats (simplified)
        total_time_entries = 0
        total_hours = 0
        billable_hours = 0

        # Storage usage (placeholder)
        storage_usage_gb = organization.get_storage_usage_gb()

        # Subscription usage
        subscription_limits = organization.get_subscription_limits()
        subscription_usage = {
            'users': {
                'used': active_members,
                'limit': subscription_limits['max_users']
            },
            'projects': {
                'used': total_projects,
                'limit': subscription_limits['max_projects']
            },
            'storage': {
                'used': storage_usage_gb,
                'limit': subscription_limits['max_storage_gb']
            }
        }

        # Growth trends (simplified - last 30 days)
        member_growth = []
        workspace_growth = []
        project_growth = []

        stats = {
            'total_members': total_members,
            'active_members': active_members,
            'total_workspaces': total_workspaces,
            'active_workspaces': active_workspaces,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'total_time_entries': total_time_entries,
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'storage_usage_gb': storage_usage_gb,
            'subscription_usage': subscription_usage,
            'member_growth': member_growth,
            'workspace_growth': workspace_growth,
            'project_growth': project_growth
        }

        serializer = OrganizationStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the organization."""
        organization = self.get_object()
        serializer = OrganizationMemberAddSerializer(
            data=request.data,
            context={'organization': organization, 'request': request}
        )

        if serializer.is_valid():
            # Create invitation
            invitation_data = {
                'organization': organization,
                'invited_by': request.user,
                'email': serializer.validated_data['email'],
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'role': serializer.validated_data['role'],
                'message': serializer.validated_data.get('message', '')
            }

            # Add workspaces if specified
            workspaces = serializer.validated_data.get('workspaces', [])
            if workspaces:
                invitation_data['workspaces'] = Workspace.objects.filter(
                    id__in=workspaces,
                    organization=organization
                )

            invitation = OrganizationInvitation.objects.create(**invitation_data)

            # Send invitation email (would implement email sending here)

            response_serializer = OrganizationInvitationSerializer(invitation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the organization."""
        organization = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': _('User ID is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            membership = OrganizationMembership.objects.get(
                organization=organization,
                user=user
            )

            # Check permissions
            if membership.role == 'owner' and organization.owner == user:
                return Response(
                    {'error': _('Cannot remove the organization owner.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            membership.deactivate()
            return Response({'message': _('Member removed successfully.')})

        except (User.DoesNotExist, OrganizationMembership.DoesNotExist):
            return Response(
                {'error': _('User is not a member of this organization.')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        """Transfer organization ownership."""
        organization = self.get_object()
        serializer = OrganizationTransferSerializer(
            data=request.data,
            context={'organization': organization}
        )

        if serializer.is_valid():
            new_owner_id = serializer.validated_data['new_owner_id']
            new_owner = User.objects.get(id=new_owner_id)

            # Update ownership
            organization.owner = new_owner
            organization.save()

            # Update membership roles
            OrganizationMembership.objects.filter(
                organization=organization,
                user=request.user,
                role='owner'
            ).update(role='admin')

            OrganizationMembership.objects.filter(
                organization=organization,
                user=new_owner
            ).update(role='owner')

            return Response({
                'message': _('Organization ownership transferred successfully.')
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_settings(self, request, pk=None):
        """Update organization settings."""
        organization = self.get_object()
        serializer = OrganizationSettingsSerializer(data=request.data)

        if serializer.is_valid():
            # Update organization fields
            for field, value in serializer.validated_data.items():
                setattr(organization, field, value)
            organization.save()

            response_serializer = OrganizationSerializer(organization)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def export_data(self, request, pk=None):
        """Export organization data."""
        organization = self.get_object()
        serializer = OrganizationExportSerializer(data=request.data)

        if serializer.is_valid():
            # Implement data export logic here
            # This would create a data export job and return a download URL
            return Response({
                'message': _('Data export started. You will receive an email when ready.'),
                'export_id': 'placeholder'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on organizations."""
        serializer = OrganizationBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            organization_ids = serializer.validated_data['organization_ids']
            action = serializer.validated_data['action']

            organizations = Organization.objects.filter(
                id__in=organization_ids,
                owner=request.user
            )

            updated_count = 0
            for organization in organizations:
                if action == 'activate':
                    organization.is_active = True
                    organization.save()
                elif action == 'deactivate':
                    organization.is_active = False
                    organization.save()
                elif action == 'delete':
                    organization.delete()
                    continue
                elif action == 'update_plan':
                    organization.subscription_plan = serializer.validated_data['subscription_plan']
                    organization.save()

                updated_count += 1

            return Response({
                'message': _('Bulk action completed successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for Workspace model."""

    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter workspaces by current user's access."""
        return Workspace.objects.filter(
            Q(organization__users=self.request.user) |
            Q(memberships__user=self.request.user, memberships__is_active=True)
        ).distinct().prefetch_related('organization', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def perform_create(self, serializer):
        """Create workspace."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get workspace statistics."""
        workspace = self.get_object()

        # Get basic counts
        total_members = workspace.get_members_count()
        active_members = workspace.memberships.filter(is_active=True).count()
        total_teams = workspace.teams.count()
        active_teams = workspace.teams.filter(is_active=True).count()
        total_projects = workspace.get_projects_count()
        active_projects = workspace.projects.filter(is_active=True).count()
        total_tasks = workspace.get_tasks_count()

        # Task completion stats
        completed_tasks = workspace.projects.aggregate(
            completed_tasks=Count('tasks', filter=Q(tasks__status='done'))
        )['completed_tasks'] or 0

        # Time entries stats (simplified)
        total_time_entries = 0
        total_hours = 0
        billable_hours = 0

        # Growth trends (simplified)
        member_growth = []
        project_growth = []
        task_completion_trend = []

        stats = {
            'total_members': total_members,
            'active_members': active_members,
            'total_teams': total_teams,
            'active_teams': active_teams,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'total_time_entries': total_time_entries,
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'member_growth': member_growth,
            'project_growth': project_growth,
            'task_completion_trend': task_completion_trend
        }

        serializer = WorkspaceStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the workspace."""
        workspace = self.get_object()
        serializer = WorkspaceMemberAddSerializer(
            data=request.data,
            context={'workspace': workspace}
        )

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            role = serializer.validated_data['role']
            team_id = serializer.validated_data.get('team_id')

            user = User.objects.get(id=user_id)
            team = Team.objects.get(id=team_id) if team_id else None

            membership, created = workspace.add_member(user, role)
            if team:
                team.add_member(user, role)

            response_serializer = WorkspaceMembershipSerializer(membership)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the workspace."""
        workspace = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': _('User ID is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            workspace.remove_member(user)
            return Response({'message': _('Member removed successfully.')})

        except User.DoesNotExist:
            return Response(
                {'error': _('User not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_settings(self, request, pk=None):
        """Update workspace settings."""
        workspace = self.get_object()
        serializer = WorkspaceSettingsSerializer(data=request.data)

        if serializer.is_valid():
            # Update workspace fields
            for field, value in serializer.validated_data.items():
                setattr(workspace, field, value)
            workspace.save()

            response_serializer = WorkspaceSerializer(workspace)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on workspaces."""
        serializer = WorkspaceBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            workspace_ids = serializer.validated_data['workspace_ids']
            action = serializer.validated_data['action']

            workspaces = Workspace.objects.filter(
                id__in=workspace_ids,
                organization__owner=request.user
            )

            updated_count = 0
            for workspace in workspaces:
                if action == 'activate':
                    workspace.is_active = True
                    workspace.save()
                elif action == 'deactivate':
                    workspace.is_active = False
                    workspace.save()
                elif action == 'delete':
                    workspace.delete()
                    continue
                elif action == 'transfer':
                    organization_id = serializer.validated_data['organization_id']
                    organization = Organization.objects.get(id=organization_id)
                    workspace.organization = organization
                    workspace.save()

                updated_count += 1

            return Response({
                'message': _('Bulk action completed successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for Team model."""

    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter teams by current user's access."""
        return Team.objects.filter(
            Q(workspace__organization__users=self.request.user) |
            Q(memberships__user=self.request.user, memberships__is_active=True)
        ).distinct().prefetch_related('workspace', 'lead', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TeamCreateSerializer
        return TeamSerializer

    def perform_create(self, serializer):
        """Create team."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get team statistics."""
        team = self.get_object()

        # Get basic counts
        total_members = team.get_members_count()
        active_members = team.memberships.filter(is_active=True).count()

        # Task stats
        total_tasks = team.memberships.aggregate(
            total_tasks=Count('user__assigned_tasks')
        )['total_tasks'] or 0

        completed_tasks = team.memberships.aggregate(
            completed_tasks=Count(
                'user__assigned_tasks',
                filter=Q(user__assigned_tasks__status='done')
            )
        )['completed_tasks'] or 0

        # Time entries stats (simplified)
        total_time_entries = 0
        total_hours = 0
        billable_hours = 0
        average_hours_per_member = total_hours / total_members if total_members > 0 else 0

        # Task completion rate
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Trends (simplified)
        productivity_trend = []
        workload_distribution = []

        stats = {
            'total_members': total_members,
            'active_members': active_members,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'total_time_entries': total_time_entries,
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'average_hours_per_member': average_hours_per_member,
            'task_completion_rate': task_completion_rate,
            'productivity_trend': productivity_trend,
            'workload_distribution': workload_distribution
        }

        serializer = TeamStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the team."""
        team = self.get_object()
        serializer = TeamMemberAddSerializer(
            data=request.data,
            context={'team': team}
        )

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            role = serializer.validated_data['role']

            user = User.objects.get(id=user_id)
            membership, created = team.add_member(user, role)

            response_serializer = TeamMembershipSerializer(membership)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the team."""
        team = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': _('User ID is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            team.remove_member(user)
            return Response({'message': _('Member removed successfully.')})

        except User.DoesNotExist:
            return Response(
                {'error': _('User not found.')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_settings(self, request, pk=None):
        """Update team settings."""
        team = self.get_object()
        serializer = TeamSettingsSerializer(data=request.data)

        if serializer.is_valid():
            # Update team fields
            for field, value in serializer.validated_data.items():
                setattr(team, field, value)
            team.save()

            response_serializer = TeamSerializer(team)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for OrganizationMembership model."""

    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter memberships by current user's organizations."""
        return OrganizationMembership.objects.filter(
            organization__users=self.request.user
        ).distinct().prefetch_related('organization', 'user', 'invited_by')


class WorkspaceMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WorkspaceMembership model."""

    serializer_class = WorkspaceMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter memberships by current user's workspaces."""
        return WorkspaceMembership.objects.filter(
            workspace__organization__users=self.request.user
        ).distinct().prefetch_related('workspace', 'user', 'team', 'added_by')


class TeamMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TeamMembership model."""

    serializer_class = TeamMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter memberships by current user's teams."""
        return TeamMembership.objects.filter(
            team__workspace__organization__users=self.request.user
        ).distinct().prefetch_related('team', 'user', 'added_by')


class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationInvitation model."""

    serializer_class = OrganizationInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter invitations by current user's organizations."""
        return OrganizationInvitation.objects.filter(
            Q(organization__users=self.request.user) |
            Q(invited_by=self.request.user)
        ).distinct().prefetch_related('organization', 'invited_by', 'workspaces')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return OrganizationInvitationCreateSerializer
        return OrganizationInvitationSerializer

    def perform_create(self, serializer):
        """Create invitation."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation."""
        invitation = self.get_object()

        if invitation.status != 'pending':
            return Response(
                {'error': _('Can only resend pending invitations.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset expiration and resend
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.save()

        # Send invitation email (would implement here)

        return Response({'message': _('Invitation resent successfully.')})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel invitation."""
        invitation = self.get_object()

        if invitation.status != 'pending':
            return Response(
                {'error': _('Can only cancel pending invitations.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = 'expired'
        invitation.save()

        return Response({'message': _('Invitation cancelled successfully.')})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept invitation."""
        invitation = self.get_object()
        user = request.user

        if invitation.status != 'pending':
            return Response(
                {'error': _('Invitation is no longer valid.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invitation.is_expired():
            return Response(
                {'error': _('Invitation has expired.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Accept invitation
        membership = invitation.accept(user)

        response_serializer = OrganizationMembershipSerializer(membership)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline invitation."""
        invitation = self.get_object()

        if invitation.status != 'pending':
            return Response(
                {'error': _('Invitation is no longer valid.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.decline()
        return Response({'message': _('Invitation declined successfully.')})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_organizations(request):
    """Get current user's organizations."""
    memberships = OrganizationMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization')

    organizations_data = []
    for membership in memberships:
        org = membership.organization
        organizations_data.append({
            'id': org.id,
            'name': org.name,
            'slug': org.slug,
            'role': membership.role,
            'is_owner': org.owner == request.user,
            'subscription_plan': org.subscription_plan,
            'member_since': membership.joined_at
        })

    return Response(organizations_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_workspaces(request):
    """Get current user's workspaces."""
    memberships = WorkspaceMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('workspace', 'workspace__organization')

    workspaces_data = []
    for membership in memberships:
        workspace = membership.workspace
        workspaces_data.append({
            'id': workspace.id,
            'name': workspace.name,
            'slug': workspace.slug,
            'organization': {
                'id': workspace.organization.id,
                'name': workspace.organization.name
            },
            'role': membership.role,
            'team': membership.team.name if membership.team else None,
            'member_since': membership.joined_at
        })

    return Response(workspaces_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_teams(request):
    """Get current user's teams."""
    memberships = TeamMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('team', 'team__workspace', 'team__workspace__organization')

    teams_data = []
    for membership in memberships:
        team = membership.team
        teams_data.append({
            'id': team.id,
            'name': team.name,
            'slug': team.slug,
            'workspace': {
                'id': team.workspace.id,
                'name': team.workspace.name,
                'organization': {
                    'id': team.workspace.organization.id,
                    'name': team.workspace.organization.name
                }
            },
            'role': membership.role,
            'lead': team.lead == request.user,
            'member_since': membership.joined_at
        })

    return Response(teams_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_permissions(request, organization_id):
    """Get user's permissions in an organization."""
    try:
        membership = OrganizationMembership.objects.get(
            organization_id=organization_id,
            user=request.user,
            is_active=True
        )

        permissions = {
            'role': membership.role,
            'permissions': membership.permissions,
            'has_permission': lambda perm: membership.has_permission(perm)
        }

        return Response(permissions)

    except OrganizationMembership.DoesNotExist:
        return Response(
            {'error': _('You are not a member of this organization.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_permissions(request, workspace_id):
    """Get user's permissions in a workspace."""
    try:
        membership = WorkspaceMembership.objects.get(
            workspace_id=workspace_id,
            user=request.user,
            is_active=True
        )

        permissions = {
            'role': membership.role,
            'permissions': membership.permissions,
            'has_permission': lambda perm: membership.has_permission(perm)
        }

        return Response(permissions)

    except WorkspaceMembership.DoesNotExist:
        return Response(
            {'error': _('You are not a member of this workspace.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_permissions(request, team_id):
    """Get user's permissions in a team."""
    try:
        membership = TeamMembership.objects.get(
            team_id=team_id,
            user=request.user,
            is_active=True
        )

        permissions = {
            'role': membership.role,
            'permissions': membership.permissions
        }

        return Response(permissions)

    except TeamMembership.DoesNotExist:
        return Response(
            {'error': _('You are not a member of this team.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invitation(request):
    """Accept organization invitation by token."""
    token = request.data.get('token')

    if not token:
        return Response(
            {'error': _('Invitation token is required.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        invitation = OrganizationInvitation.objects.get(
            token=token,
            status='pending'
        )

        if invitation.is_expired():
            return Response(
                {'error': _('Invitation has expired.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Accept invitation
        membership = invitation.accept(request.user)

        response_serializer = OrganizationMembershipSerializer(membership)
        return Response(response_serializer.data)

    except OrganizationInvitation.DoesNotExist:
        return Response(
            {'error': _('Invalid invitation token.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_hierarchy(request, organization_id):
    """Get organization hierarchy."""
    try:
        organization = Organization.objects.get(id=organization_id)

        # Check access
        if not OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).exists():
            return Response(
                {'error': _('You are not a member of this organization.')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Build hierarchy
        workspaces = organization.workspaces.filter(is_active=True)
        hierarchy = {
            'organization': OrganizationSerializer(organization).data,
            'workspaces': []
        }

        for workspace in workspaces:
            workspace_data = WorkspaceSerializer(workspace).data
            workspace_data['teams'] = []

            teams = workspace.teams.filter(is_active=True)
            for team in teams:
                team_data = TeamSerializer(team).data
                team_data['members'] = TeamMembershipSerializer(
                    team.memberships.filter(is_active=True),
                    many=True
                ).data
                workspace_data['teams'].append(team_data)

            workspace_data['members'] = WorkspaceMembershipSerializer(
                workspace.memberships.filter(is_active=True),
                many=True
            ).data

            hierarchy['workspaces'].append(workspace_data)

        return Response(hierarchy)

    except Organization.DoesNotExist:
        return Response(
            {'error': _('Organization not found.')},
            status=status.HTTP_404_NOT_FOUND
        )