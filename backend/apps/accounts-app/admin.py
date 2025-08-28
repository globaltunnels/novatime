"""
Admin configuration for accounts app.

This module configures the Django admin interface for user-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from .models import (
    User, UserProfile, UserSession, PasswordResetToken,
    EmailVerificationToken, UserActivity
)

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model."""

    list_display = [
        'email', 'first_name', 'last_name', 'is_active', 'is_verified',
        'is_staff', 'is_superuser', 'organizations_count', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_verified', 'is_staff', 'is_superuser',
        'two_factor_enabled', 'passkeys_enabled', 'created_at'
    ]
    search_fields = [
        'email', 'first_name', 'last_name', 'phone'
    ]
    readonly_fields = [
        'id', 'organizations_count', 'workspaces_count', 'teams_count',
        'created_at', 'updated_at', 'last_login_at', 'last_activity_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('email', 'first_name', 'last_name', 'password')
        }),
        (_('Profile Information'), {
            'fields': ('avatar_url', 'bio', 'title', 'department', 'phone')
        }),
        (_('Preferences'), {
            'fields': ('timezone', 'language', 'work_hours_start', 'work_hours_end', 'work_days')
        }),
        (_('Notifications'), {
            'fields': ('email_notifications', 'push_notifications', 'weekly_digest')
        }),
        (_('Privacy'), {
            'fields': ('profile_visibility', 'show_online_status')
        }),
        (_('Security'), {
            'fields': ('two_factor_enabled', 'passkeys_enabled', 'is_active', 'is_verified')
        }),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Statistics'), {
            'fields': ('organizations_count', 'workspaces_count', 'teams_count'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'last_login_at', 'last_activity_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (_('Create User'), {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    actions = [
        'activate_users', 'deactivate_users', 'verify_users', 'unverify_users',
        'enable_two_factor', 'disable_two_factor'
    ]

    def organizations_count(self, obj):
        """Display organizations count."""
        return obj.get_organizations().count()
    organizations_count.short_description = _('Organizations')

    def workspaces_count(self, obj):
        """Display workspaces count."""
        return obj.get_workspaces().count()
    workspaces_count.short_description = _('Workspaces')

    def teams_count(self, obj):
        """Display teams count."""
        return obj.get_teams().count()
    teams_count.short_description = _('Teams')

    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d user was successfully activated.',
                '%d users were successfully activated.',
                updated,
            ) % updated,
        )
    activate_users.short_description = _('Activate selected users')

    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d user was successfully deactivated.',
                '%d users were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_users.short_description = _('Deactivate selected users')

    def verify_users(self, request, queryset):
        """Verify selected users."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            ngettext(
                '%d user was successfully verified.',
                '%d users were successfully verified.',
                updated,
            ) % updated,
        )
    verify_users.short_description = _('Verify selected users')

    def unverify_users(self, request, queryset):
        """Unverify selected users."""
        updated = queryset.update(is_verified=False)
        self.message_user(
            request,
            ngettext(
                '%d user was successfully unverified.',
                '%d users were successfully unverified.',
                updated,
            ) % updated,
        )
    unverify_users.short_description = _('Unverify selected users')

    def enable_two_factor(self, request, queryset):
        """Enable two-factor authentication for selected users."""
        updated = 0
        for user in queryset:
            user.enable_two_factor()
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d user had two-factor authentication enabled.',
                '%d users had two-factor authentication enabled.',
                updated,
            ) % updated,
        )
    enable_two_factor.short_description = _('Enable two-factor authentication')

    def disable_two_factor(self, request, queryset):
        """Disable two-factor authentication for selected users."""
        updated = 0
        for user in queryset:
            user.disable_two_factor()
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d user had two-factor authentication disabled.',
                '%d users had two-factor authentication disabled.',
                updated,
            ) % updated,
        )
    disable_two_factor.short_description = _('Disable two-factor authentication')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""

    list_display = [
        'user', 'completion_percentage', 'theme', 'work_style', 'created_at'
    ]
    list_filter = [
        'theme', 'work_style', 'data_sharing', 'marketing_emails', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'location'
    ]
    readonly_fields = [
        'id', 'completion_percentage', 'created_at', 'updated_at'
    ]
    ordering = ['user']

    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Personal Information'), {
            'fields': ('date_of_birth', 'gender', 'location'),
            'classes': ('collapse',)
        }),
        (_('Professional Information'), {
            'fields': ('years_of_experience', 'skills', 'certifications'),
            'classes': ('collapse',)
        }),
        (_('Social Links'), {
            'fields': ('linkedin_url', 'github_url', 'twitter_handle', 'website_url'),
            'classes': ('collapse',)
        }),
        (_('Preferences'), {
            'fields': ('theme', 'date_format', 'time_format', 'currency', 'work_style')
        }),
        (_('Work Preferences'), {
            'fields': ('meeting_availability',),
            'classes': ('collapse',)
        }),
        (_('Notification Settings'), {
            'fields': ('notification_preferences',),
            'classes': ('collapse',)
        }),
        (_('Privacy Settings'), {
            'fields': ('data_sharing', 'marketing_emails'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('completion_percentage',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['update_completion_percentage']

    def update_completion_percentage(self, request, queryset):
        """Update completion percentage for selected profiles."""
        updated = 0
        for profile in queryset:
            profile.save()  # This will trigger the save method that updates completion_percentage
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d profile completion percentage was updated.',
                '%d profile completion percentages were updated.',
                updated,
            ) % updated,
        )
    update_completion_percentage.short_description = _('Update completion percentage')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin for UserSession model."""

    list_display = [
        'user', 'device_type', 'device_name', 'ip_address', 'is_active',
        'is_expired', 'created_at', 'last_activity_at'
    ]
    list_filter = [
        'device_type', 'is_active', 'created_at', 'last_activity_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'ip_address', 'device_name'
    ]
    readonly_fields = [
        'id', 'session_key', 'is_expired', 'created_at', 'last_activity_at', 'expires_at'
    ]
    ordering = ['-last_activity_at']

    fieldsets = (
        (_('Session'), {
            'fields': ('user', 'session_key')
        }),
        (_('Device Information'), {
            'fields': ('device_type', 'device_name', 'browser', 'ip_address', 'user_agent')
        }),
        (_('Location'), {
            'fields': ('location',),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_expired')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_activity_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_sessions', 'deactivate_sessions', 'extend_sessions']

    def is_expired(self, obj):
        """Display if session is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expired')

    def activate_sessions(self, request, queryset):
        """Activate selected sessions."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                '%d session was successfully activated.',
                '%d sessions were successfully activated.',
                updated,
            ) % updated,
        )
    activate_sessions.short_description = _('Activate selected sessions')

    def deactivate_sessions(self, request, queryset):
        """Deactivate selected sessions."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                '%d session was successfully deactivated.',
                '%d sessions were successfully deactivated.',
                updated,
            ) % updated,
        )
    deactivate_sessions.short_description = _('Deactivate selected sessions')

    def extend_sessions(self, request, queryset):
        """Extend selected sessions."""
        updated = 0
        for session in queryset:
            session.extend(hours=24)
            updated += 1
        self.message_user(
            request,
            ngettext(
                '%d session was successfully extended.',
                '%d sessions were successfully extended.',
                updated,
            ) % updated,
        )
    extend_sessions.short_description = _('Extend selected sessions')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for PasswordResetToken model."""

    list_display = [
        'user', 'is_used', 'is_expired', 'created_at', 'expires_at', 'used_at'
    ]
    list_filter = [
        'is_used', 'created_at', 'expires_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'token'
    ]
    readonly_fields = [
        'id', 'token', 'is_expired', 'created_at', 'used_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Token'), {
            'fields': ('user', 'token')
        }),
        (_('Status'), {
            'fields': ('is_used', 'is_expired')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at', 'used_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['expire_tokens']

    def is_expired(self, obj):
        """Display if token is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expired')

    def expire_tokens(self, request, queryset):
        """Expire selected tokens."""
        updated = queryset.filter(is_used=False).update(
            expires_at=timezone.now() - timezone.timedelta(seconds=1)
        )
        self.message_user(
            request,
            ngettext(
                '%d token was successfully expired.',
                '%d tokens were successfully expired.',
                updated,
            ) % updated,
        )
    expire_tokens.short_description = _('Expire selected tokens')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for EmailVerificationToken model."""

    list_display = [
        'user', 'email', 'is_verified', 'is_expired', 'created_at', 'expires_at'
    ]
    list_filter = [
        'is_verified', 'created_at', 'expires_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'email', 'token'
    ]
    readonly_fields = [
        'id', 'token', 'is_expired', 'created_at', 'verified_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Token'), {
            'fields': ('user', 'email', 'token')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_expired')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['verify_emails', 'expire_tokens']

    def is_expired(self, obj):
        """Display if token is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expired')

    def verify_emails(self, request, queryset):
        """Verify selected emails."""
        updated = 0
        for token in queryset:
            if token.verify():
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d email was successfully verified.',
                '%d emails were successfully verified.',
                updated,
            ) % updated,
        )
    verify_emails.short_description = _('Verify selected emails')

    def expire_tokens(self, request, queryset):
        """Expire selected tokens."""
        updated = queryset.filter(is_verified=False).update(
            expires_at=timezone.now() - timezone.timedelta(seconds=1)
        )
        self.message_user(
            request,
            ngettext(
                '%d token was successfully expired.',
                '%d tokens were successfully expired.',
                updated,
            ) % updated,
        )
    expire_tokens.short_description = _('Expire selected tokens')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for UserActivity model."""

    list_display = [
        'user', 'action', 'category', 'organization', 'workspace', 'created_at'
    ]
    list_filter = [
        'category', 'action', 'created_at', 'organization', 'workspace'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'action', 'description'
    ]
    readonly_fields = [
        'id', 'created_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Activity'), {
            'fields': ('user', 'action', 'description', 'category')
        }),
        (_('Context'), {
            'fields': ('ip_address', 'user_agent', 'metadata')
        }),
        (_('Organization Context'), {
            'fields': ('organization', 'workspace'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_activities']

    def export_activities(self, request, queryset):
        """Export selected activities."""
        # Implementation would create a CSV/JSON export
        self.message_user(
            request,
            _('Activities export functionality would be implemented here.')
        )
    export_activities.short_description = _('Export selected activities')


# Inline admin classes
class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserSessionInline(admin.TabularInline):
    """Inline admin for UserSession model."""
    model = UserSession
    extra = 0
    fields = ['device_type', 'device_name', 'ip_address', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


class UserActivityInline(admin.TabularInline):
    """Inline admin for UserActivity model."""
    model = UserActivity
    extra = 0
    fields = ['action', 'category', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


# Add inlines to User admin
CustomUserAdmin.inlines = [
    UserProfileInline,
    UserSessionInline,
    UserActivityInline
]