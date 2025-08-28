"""
Admin configuration for time entries app.

This module configures the Django admin interface for time entry-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    TimeEntry, Timer, IdlePeriod, TimeEntryTemplate, TimeEntryComment
)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    """Admin for TimeEntry model."""

    list_display = [
        'user', 'task', 'project', 'start_time', 'duration_minutes',
        'is_billable', 'cost_amount', 'is_approved', 'created_at'
    ]
    list_filter = [
        'workspace', 'is_billable', 'is_approved', 'start_time',
        'device_type', 'operating_system', 'ai_generated'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'task__title', 'project__name', 'description'
    ]
    readonly_fields = [
        'id', 'duration_minutes', 'cost_amount', 'created_at', 'updated_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'workspace', 'task', 'project', 'description')
        }),
        (_('Time Tracking'), {
            'fields': ('start_time', 'end_time', 'duration_minutes')
        }),
        (_('Billing & Cost'), {
            'fields': ('is_billable', 'hourly_rate', 'cost_amount')
        }),
        (_('Quality & AI'), {
            'fields': ('productivity_score', 'focus_score', 'idle_minutes',
                      'ai_generated', 'ai_confidence'),
            'classes': ('collapse',)
        }),
        (_('Location & Device'), {
            'fields': ('location', 'ip_address', 'user_agent', 'device_type',
                      'operating_system'),
            'classes': ('collapse',)
        }),
        (_('Tags & Custom Fields'), {
            'fields': ('tags', 'custom_fields'),
            'classes': ('collapse',)
        }),
        (_('Approval'), {
            'fields': ('is_approved', 'approved_by', 'approved_at', 'approval_notes'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    """Admin for Timer model."""

    list_display = [
        'user', 'task', 'project', 'start_time', 'status',
        'current_duration_display', 'is_billable', 'created_at'
    ]
    list_filter = [
        'workspace', 'status', 'is_billable', 'start_time'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'task__title', 'project__name', 'description'
    ]
    readonly_fields = [
        'id', 'paused_at', 'total_paused_minutes', 'created_at', 'updated_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'workspace', 'task', 'project', 'description')
        }),
        (_('Timer State'), {
            'fields': ('start_time', 'paused_at', 'total_paused_minutes', 'status')
        }),
        (_('Settings'), {
            'fields': ('is_billable', 'hourly_rate', 'idle_threshold_minutes',
                      'auto_stop_on_idle', 'track_location')
        }),
        (_('Metadata'), {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

    def current_duration_display(self, obj):
        """Display current duration."""
        return obj.get_current_duration_display()
    current_duration_display.short_description = _('Current Duration')


@admin.register(IdlePeriod)
class IdlePeriodAdmin(admin.ModelAdmin):
    """Admin for IdlePeriod model."""

    list_display = [
        'time_entry', 'start_time', 'end_time', 'duration_minutes',
        'detection_method', 'created_at'
    ]
    list_filter = [
        'detection_method', 'start_time', 'created_at'
    ]
    search_fields = [
        'time_entry__user__email', 'time_entry__task__title',
        'active_application', 'active_window_title'
    ]
    readonly_fields = [
        'id', 'duration_minutes', 'created_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Idle Period'), {
            'fields': ('time_entry', 'start_time', 'end_time', 'duration_minutes')
        }),
        (_('Detection'), {
            'fields': ('detection_method', 'active_application', 'active_window_title')
        }),
        (_('Metadata'), {
            'fields': ('created_at',)
        }),
    )


@admin.register(TimeEntryTemplate)
class TimeEntryTemplateAdmin(admin.ModelAdmin):
    """Admin for TimeEntryTemplate model."""

    list_display = [
        'name', 'user', 'workspace', 'task_type', 'priority',
        'usage_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'workspace', 'task_type', 'priority', 'is_active', 'is_public'
    ]
    search_fields = ['name', 'description', 'user__email']
    readonly_fields = [
        'id', 'usage_count', 'created_at', 'updated_at', 'user'
    ]
    ordering = ['-usage_count', 'name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'workspace', 'name', 'description')
        }),
        (_('Template Settings'), {
            'fields': ('task_type', 'priority', 'is_public')
        }),
        (_('Defaults'), {
            'fields': ('default_duration_minutes', 'default_is_billable',
                      'default_hourly_rate')
        }),
        (_('Recurrence'), {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_interval'),
            'classes': ('collapse',)
        }),
        (_('Template Data'), {
            'fields': ('template_data',),
            'classes': ('collapse',)
        }),
        (_('Usage'), {
            'fields': ('usage_count', 'is_active')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TimeEntryComment)
class TimeEntryCommentAdmin(admin.ModelAdmin):
    """Admin for TimeEntryComment model."""

    list_display = [
        'time_entry', 'author', 'comment_type', 'is_private', 'created_at'
    ]
    list_filter = [
        'comment_type', 'is_private', 'created_at'
    ]
    search_fields = [
        'content', 'time_entry__user__email', 'author__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Comment'), {
            'fields': ('time_entry', 'author', 'content', 'comment_type', 'is_private')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


# Inline admin classes for related models
class TimeEntryInline(admin.TabularInline):
    """Inline admin for TimeEntry model."""
    model = TimeEntry
    extra = 0
    fields = ['task', 'start_time', 'duration_minutes', 'is_billable', 'is_approved']
    readonly_fields = ['created_at']
    show_change_view = True


class TimerInline(admin.TabularInline):
    """Inline admin for Timer model."""
    model = Timer
    extra = 0
    fields = ['task', 'start_time', 'status', 'is_billable']
    readonly_fields = ['created_at']
    show_change_view = True


class IdlePeriodInline(admin.TabularInline):
    """Inline admin for IdlePeriod model."""
    model = IdlePeriod
    extra = 0
    fields = ['start_time', 'duration_minutes', 'detection_method']
    readonly_fields = ['created_at']
    show_change_view = True


class TimeEntryCommentInline(admin.TabularInline):
    """Inline admin for TimeEntryComment model."""
    model = TimeEntryComment
    extra = 0
    fields = ['author', 'content', 'comment_type', 'is_private']
    readonly_fields = ['created_at']
    show_change_view = True


# Add inlines to related models
# Note: These would be added to User, Task, and Project admin classes in their respective apps