"""
Admin configuration for organizations app.

This module configures the Django admin interface for organization-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta


from .models import (
    Organization, Workspace, Team, OrganizationMembership,
    WorkspaceMembership, TeamMembership, OrganizationInvitation
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin for Organization model."""

    list_display = [
        'name', 'slug', 'owner', 'subscription_plan', 'is_active',
        'is_verified', 'members_count', 'workspaces_count', 'created_at'
    ]
    list_filter = [
        'subscription_plan', 'subscription_status', 'is_active', 'is_verified',
        'industry', 'company_size', 'created_at'
    ]
    search_fields = [
        'name', 'slug', 'email', 'website', 'owner__email', 'owner__first_name', 'owner__last_name'
    ]
    readonly_fields = [
        'id', 'members_count', 'active_users_count', 'workspaces_count',
        'projects_count', 'storage_usage_gb', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description', 'website', 'email', 'phone')
        }),
        (_('Address'), {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        (_('Business Information'), {
            'fields': ('industry', 'company_size',),
            'classes': ('collapse',)
        }),
        (_('Branding'), {
            'fields': ('logo_url', 'primary_color', 'secondary_color'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('timezone', 'date_format', 'currency', 'language'),
            'classes': ('collapse',)
        }),
        (_('Subscription'), {
            'fields': ('subscription_plan', 'subscription_status', 'trial_end_date', 'max_users', 'max_projects', 'max_storage_gb'),
            'classes': ('collapse',)
        }),
        (_('Features'), {
            'fields': ('features_enabled', 'is_active', 'is_verified'),
            'classes': ('collapse',)
        }),
        (_('Ownership'), {
            'fields': ('created_by', 'owner'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('members_count', 'active_users_count', 'workspaces_count', 'projects_count', 'storage_usage_gb'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_organizations', 'deactivate_organizations', 'verify_organizations']

    def members_count(self, obj):
        """Display members count."""
        return obj.get_members_count()
    members_count.short_description = _('Members')

    def workspaces_count(self, obj):
        """Display workspaces count."""
        return obj.get_workspaces_count()
    workspaces_count.short_description = _('Workspaces')

    def activate_organizations(self, request, queryset):
        """Activate selected organizations."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d organization was successfully activated.',
                '%d organizations were successfully activated.',
                updated,
            ) % updated,
        )
    activate_organizations.short_description = _('Activate selected organizations')

    def deactivate_organizations(self, request, queryset):
        """Deactivate selected organizations."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d organization was successfully deactivated.',
                '%d organizations were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_organizations.short_description = _('Deactivate selected organizations')

    def verify_organizations(self, request, queryset):
        """Verify selected organizations."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            ngettext(
                '%d organization was successfully verified.',
                '%d organizations were successfully verified.',
                updated,
            ) % updated,
        )
    verify_organizations.short_description = _('Verify selected organizations')


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """Admin for Workspace model."""

    list_display = [
        'name', 'slug', 'organization', 'is_active', 'is_private',
        'members_count', 'projects_count', 'teams_count', 'created_at'
    ]
    list_filter = [
        'organization', 'is_active', 'is_private', 'created_at'
    ]
    search_fields = [
        'name', 'slug', 'organization__name', 'description'
    ]
    readonly_fields = [
        'id', 'members_count', 'projects_count', 'tasks_count', 'teams_count',
        'created_at', 'updated_at'
    ]
    ordering = ['organization', '-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description', 'organization')
        }),
        (_('Settings'), {
            'fields': ('timezone', 'currency', 'is_active', 'is_private')
        }),
        (_('Ownership'), {
            'fields': ('created_by',)
        }),
        (_('Statistics'), {
            'fields': ('members_count', 'projects_count', 'tasks_count', 'teams_count'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_workspaces', 'deactivate_workspaces']

    def members_count(self, obj):
        """Display members count."""
        return obj.get_members_count()
    members_count.short_description = _('Members')

    def projects_count(self, obj):
        """Display projects count."""
        return obj.get_projects_count()
    projects_count.short_description = _('Projects')

    def teams_count(self, obj):
        """Display teams count."""
        return obj.teams.count()
    teams_count.short_description = _('Teams')

    def activate_workspaces(self, request, queryset):
        """Activate selected workspaces."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d workspace was successfully activated.',
                '%d workspaces were successfully activated.',
                updated,
            ) % updated,
        )
    activate_workspaces.short_description = _('Activate selected workspaces')

    def deactivate_workspaces(self, request, queryset):
        """Deactivate selected workspaces."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d workspace was successfully deactivated.',
                '%d workspaces were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_workspaces.short_description = _('Deactivate selected workspaces')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""

    list_display = [
        'name', 'slug', 'workspace', 'lead', 'is_active',
        'members_count', 'created_at'
    ]
    list_filter = [
        'workspace', 'workspace__organization', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'slug', 'workspace__name', 'description', 'lead__email'
    ]
    readonly_fields = [
        'id', 'members_count', 'created_at', 'updated_at'
    ]
    ordering = ['workspace', '-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description', 'workspace')
        }),
        (_('Leadership'), {
            'fields': ('lead', 'color')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Ownership'), {
            'fields': ('created_by',)
        }),
        (_('Statistics'), {
            'fields': ('members_count',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_teams', 'deactivate_teams']

    def members_count(self, obj):
        """Display members count."""
        return obj.get_members_count()
    members_count.short_description = _('Members')

    def activate_teams(self, request, queryset):
        """Activate selected teams."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d team was successfully activated.',
                '%d teams were successfully activated.',
                updated,
            ) % updated,
        )
    activate_teams.short_description = _('Activate selected teams')

    def deactivate_teams(self, request, queryset):
        """Deactivate selected teams."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d team was successfully deactivated.',
                '%d teams were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_teams.short_description = _('Deactivate selected teams')


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin for OrganizationMembership model."""

    list_display = [
        'user', 'organization', 'role', 'is_active', 'joined_at', 'invited_at'
    ]
    list_filter = [
        'organization', 'role', 'is_active', 'joined_at', 'invited_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'organization__name'
    ]
    readonly_fields = [
        'id', 'joined_at', 'invited_at', 'created_at', 'updated_at'
    ]
    ordering = ['organization', '-joined_at']

    fieldsets = (
        (_('Membership'), {
            'fields': ('organization', 'user', 'role')
        }),
        (_('Status'), {
            'fields': ('is_active', 'permissions')
        }),
        (_('Timeline'), {
            'fields': ('invited_at', 'joined_at', 'invited_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_memberships', 'deactivate_memberships']

    def activate_memberships(self, request, queryset):
        """Activate selected memberships."""
        updated = 0
        for membership in queryset:
            membership.activate()
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully activated.',
                '%d memberships were successfully activated.',
                updated,
            ) % updated,
        )
    activate_memberships.short_description = _('Activate selected memberships')

    def deactivate_memberships(self, request, queryset):
        """Deactivate selected memberships."""
        updated = 0
        for membership in queryset:
            membership.deactivate()
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully deactivated.',
                '%d memberships were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_memberships.short_description = _('Deactivate selected memberships')


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    """Admin for WorkspaceMembership model."""

    list_display = [
        'user', 'workspace', 'team', 'role', 'is_active', 'joined_at'
    ]
    list_filter = [
        'workspace', 'workspace__organization', 'team', 'role', 'is_active', 'joined_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'workspace__name', 'team__name'
    ]
    readonly_fields = [
        'id', 'joined_at', 'created_at', 'updated_at'
    ]
    ordering = ['workspace', '-joined_at']

    fieldsets = (
        (_('Membership'), {
            'fields': ('workspace', 'user', 'team', 'role')
        }),
        (_('Status'), {
            'fields': ('is_active', 'permissions')
        }),
        (_('Timeline'), {
            'fields': ('joined_at', 'added_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_memberships', 'deactivate_memberships']

    def activate_memberships(self, request, queryset):
        """Activate selected memberships."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully activated.',
                '%d memberships were successfully activated.',
                updated,
            ) % updated,
        )
    activate_memberships.short_description = _('Activate selected memberships')

    def deactivate_memberships(self, request, queryset):
        """Deactivate selected memberships."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully deactivated.',
                '%d memberships were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_memberships.short_description = _('Deactivate selected memberships')


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    """Admin for TeamMembership model."""

    list_display = [
        'user', 'team', 'role', 'is_active', 'joined_at'
    ]
    list_filter = [
        'team', 'team__workspace', 'team__workspace__organization', 'role', 'is_active', 'joined_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'team__name'
    ]
    readonly_fields = [
        'id', 'joined_at', 'created_at', 'updated_at'
    ]
    ordering = ['team', '-joined_at']

    fieldsets = (
        (_('Membership'), {
            'fields': ('team', 'user', 'role')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timeline'), {
            'fields': ('joined_at', 'added_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_memberships', 'deactivate_memberships']

    def activate_memberships(self, request, queryset):
        """Activate selected memberships."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully activated.',
                '%d memberships were successfully activated.',
                updated,
            ) % updated,
        )
    activate_memberships.short_description = _('Activate selected memberships')

    def deactivate_memberships(self, request, queryset):
        """Deactivate selected memberships."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d membership was successfully deactivated.',
                '%d memberships were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_memberships.short_description = _('Deactivate selected memberships')


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    """Admin for OrganizationInvitation model."""

    list_display = [
        'email', 'organization', 'role', 'status', 'sent_at', 'expires_at', 'is_expired'
    ]
    list_filter = [
        'organization', 'role', 'status', 'sent_at', 'expires_at'
    ]
    search_fields = [
        'email', 'first_name', 'last_name', 'organization__name', 'invited_by__email'
    ]
    readonly_fields = [
        'id', 'token', 'sent_at', 'responded_at', 'is_expired', 'created_at', 'updated_at'
    ]
    ordering = ['-sent_at']

    fieldsets = (
        (_('Invitation'), {
            'fields': ('organization', 'invited_by', 'email', 'first_name', 'last_name')
        }),
        (_('Details'), {
            'fields': ('role', 'workspaces', 'message')
        }),
        (_('Status'), {
            'fields': ('status', 'token', 'sent_at', 'responded_at', 'expires_at', 'is_expired')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['resend_invitations', 'cancel_invitations', 'expire_invitations']

    def is_expired(self, obj):
        """Display if invitation is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expired')

    def resend_invitations(self, request, queryset):
        """Resend selected invitations."""
        updated = 0
        for invitation in queryset:
            if invitation.status == 'pending':
                invitation.expires_at = timezone.now() + timedelta(days=7)
                invitation.save()
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d invitation was successfully resent.',
                '%d invitations were successfully resent.',
                updated,
            ) % updated,
        )
    resend_invitations.short_description = _('Resend selected invitations')

    def cancel_invitations(self, request, queryset):
        """Cancel selected invitations."""
        updated = queryset.filter(status='pending').update(status='expired')
        self.message_user(
            request,
            ngettext(
                '%d invitation was successfully cancelled.',
                '%d invitations were successfully cancelled.',
                updated,
            ) % updated,
        )
    cancel_invitations.short_description = _('Cancel selected invitations')

    def expire_invitations(self, request, queryset):
        """Expire selected invitations."""
        updated = queryset.filter(status='pending').update(status='expired')
        self.message_user(
            request,
            ngettext(
                '%d invitation was successfully expired.',
                '%d invitations were successfully expired.',
                updated,
            ) % updated,
        )
    expire_invitations.short_description = _('Expire selected invitations')


# Inline admin classes
class WorkspaceInline(admin.TabularInline):
    """Inline admin for Workspace model."""
    model = Workspace
    extra = 0
    fields = ['name', 'slug', 'is_active', 'is_private', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


class TeamInline(admin.TabularInline):
    """Inline admin for Team model."""
    model = Team
    extra = 0
    fields = ['name', 'slug', 'lead', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


class OrganizationMembershipInline(admin.TabularInline):
    """Inline admin for OrganizationMembership model."""
    model = OrganizationMembership
    extra = 0
    fields = ['user', 'role', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']
    show_change_view = True


class WorkspaceMembershipInline(admin.TabularInline):
    """Inline admin for WorkspaceMembership model."""
    model = WorkspaceMembership
    extra = 0
    fields = ['user', 'team', 'role', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']
    show_change_view = True


class TeamMembershipInline(admin.TabularInline):
    """Inline admin for TeamMembership model."""
    model = TeamMembership
    extra = 0
    fields = ['user', 'role', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']
    show_change_view = True


class OrganizationInvitationInline(admin.TabularInline):
    """Inline admin for OrganizationInvitation model."""
    model = OrganizationInvitation
    extra = 0
    fields = ['email', 'role', 'status', 'sent_at', 'expires_at']
    readonly_fields = ['sent_at', 'expires_at']
    show_change_view = True


# Add inlines to Organization admin
OrganizationAdmin.inlines = [
    WorkspaceInline,
    OrganizationMembershipInline,
    OrganizationInvitationInline
]

# Add inlines to Workspace admin
WorkspaceAdmin.inlines = [
    TeamInline,
    WorkspaceMembershipInline
]

# Add inlines to Team admin
TeamAdmin.inlines = [
    TeamMembershipInline
]