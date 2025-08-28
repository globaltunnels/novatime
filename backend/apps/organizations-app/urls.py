"""
URL configuration for organizations app.

This module defines URL patterns for the organizations API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OrganizationViewSet, WorkspaceViewSet, TeamViewSet,
    OrganizationMembershipViewSet, WorkspaceMembershipViewSet,
    TeamMembershipViewSet, OrganizationInvitationViewSet,
    my_organizations, my_workspaces, my_teams, organization_permissions,
    workspace_permissions, team_permissions, accept_invitation,
    organization_hierarchy
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'organization-memberships', OrganizationMembershipViewSet, basename='organization-membership')
router.register(r'workspace-memberships', WorkspaceMembershipViewSet, basename='workspace-membership')
router.register(r'team-memberships', TeamMembershipViewSet, basename='team-membership')
router.register(r'organisation-invitations', OrganizationInvitationViewSet, basename='organization-invitation')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints
    path('my-organizations/', my_organizations, name='my-organizations'),
    path('my-workspaces/', my_workspaces, name='my-workspaces'),
    path('my-teams/', my_teams, name='my-teams'),
    path('organizations/<uuid:organization_id>/permissions/', organization_permissions, name='organization-permissions'),
    path('workspaces/<uuid:workspace_id>/permissions/', workspace_permissions, name='workspace-permissions'),
    path('teams/<uuid:team_id>/permissions/', team_permissions, name='team-permissions'),
    path('accept-invitation/', accept_invitation, name='accept-invitation'),
    path('organizations/<uuid:organization_id>/hierarchy/', organization_hierarchy, name='organization-hierarchy'),
]