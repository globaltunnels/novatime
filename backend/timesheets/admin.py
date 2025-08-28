"""
Admin configuration for timesheets app.

This module configures the Django admin interface for timesheet-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    TimesheetPeriod, Timesheet, TimesheetEntry, ApprovalWorkflow,
    TimesheetComment, TimesheetTemplate
)


@admin.register(TimesheetPeriod)
class TimesheetPeriodAdmin(admin.ModelAdmin):
    """Admin for TimesheetPeriod model."""

    list_display = [
        'name', 'workspace', 'period_type', 'start_date', 'end_date',
        'is_active', 'get_total_users', 'get_submitted_count', 'get_completion_percentage'
    ]
    list_filter = [
        'workspace', 'period_type', 'is_active', 'start_date', 'end_date'
    ]
    search_fields = ['name', 'workspace__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'get_total_users', 'get_submitted_count', 'get_completion_percentage'
    ]
    ordering = ['workspace', '-start_date']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('workspace', 'name', 'period_type')
        }),
        (_('Period Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Settings'), {
            'fields': ('is_active', 'auto_create_timesheets', 'submission_deadline_days',
                      'require_approval', 'auto_approve_after_days')
        }),
        (_('Statistics'), {
            'fields': ('get_total_users', 'get_submitted_count', 'get_completion_percentage'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def get_total_users(self, obj):
        """Get total users count."""
        return obj.get_total_users()
    get_total_users.short_description = _('Total Users')

    def get_submitted_count(self, obj):
        """Get submitted count."""
        return obj.get_submitted_count()
    get_submitted_count.short_description = _('Submitted')

    def get_completion_percentage(self, obj):
        """Get completion percentage."""
        return f"{obj.get_completion_percentage()}%"
    get_completion_percentage.short_description = _('Completion %')


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    """Admin for Timesheet model."""

    list_display = [
        'id', 'user', 'period', 'status', 'total_hours', 'billable_hours',
        'total_cost', 'submitted_at', 'approved_at'
    ]
    list_filter = [
        'workspace', 'period', 'status', 'submitted_at', 'approved_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'period__name'
    ]
    readonly_fields = [
        'id', 'total_hours', 'billable_hours', 'total_cost',
        'quality_score', 'created_at', 'updated_at'
    ]
    ordering = ['user', '-period__start_date']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'workspace', 'period', 'title')
        }),
        (_('Status & Approval'), {
            'fields': ('status', 'submitted_at', 'approved_at', 'approved_by',
                      'rejection_reason', 'approval_workflow')
        }),
        (_('Time & Cost'), {
            'fields': ('total_hours', 'billable_hours', 'total_cost')
        }),
        (_('Quality'), {
            'fields': ('quality_score', 'quality_issues'),
            'classes': ('collapse',)
        }),
        (_('AI & Automation'), {
            'fields': ('ai_generated', 'ai_suggestions'),
            'classes': ('collapse',)
        }),
        (_('Custom Fields'), {
            'fields': ('custom_fields',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related(
            'user', 'workspace', 'period', 'approved_by', 'approval_workflow'
        )


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    """Admin for TimesheetEntry model."""

    list_display = [
        'id', 'timesheet', 'time_entry', 'get_effective_hours', 'get_effective_rate'
    ]
    list_filter = [
        'timesheet__period', 'timesheet__status'
    ]
    search_fields = [
        'timesheet__user__email', 'timesheet__period__name',
        'time_entry__description'
    ]
    readonly_fields = [
        'id', 'get_effective_hours', 'get_effective_rate', 'created_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Entry Information'), {
            'fields': ('timesheet', 'time_entry')
        }),
        (_('Adjustments'), {
            'fields': ('notes', 'adjusted_hours', 'adjusted_rate')
        }),
        (_('Calculated Values'), {
            'fields': ('get_effective_hours', 'get_effective_rate'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related(
            'timesheet__user', 'timesheet__period', 'time_entry'
        )


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    """Admin for ApprovalWorkflow model."""

    list_display = [
        'name', 'workspace', 'workflow_type', 'is_active', 'is_default'
    ]
    list_filter = [
        'workspace', 'workflow_type', 'is_active', 'is_default'
    ]
    search_fields = ['name', 'description', 'workspace__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    ordering = ['workspace', 'name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('workspace', 'name', 'description', 'workflow_type')
        }),
        (_('Configuration'), {
            'fields': ('steps', 'conditions', 'auto_approve_rules'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('is_active', 'is_default')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(TimesheetComment)
class TimesheetCommentAdmin(admin.ModelAdmin):
    """Admin for TimesheetComment model."""

    list_display = [
        'id', 'timesheet', 'author', 'comment_type', 'is_private', 'created_at'
    ]
    list_filter = [
        'comment_type', 'is_private', 'created_at'
    ]
    search_fields = [
        'content', 'timesheet__user__email', 'author__email'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('Comment'), {
            'fields': ('timesheet', 'author', 'content', 'comment_type', 'is_private')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related(
            'timesheet__user', 'author'
        )


@admin.register(TimesheetTemplate)
class TimesheetTemplateAdmin(admin.ModelAdmin):
    """Admin for TimesheetTemplate model."""

    list_display = [
        'name', 'workspace', 'usage_count', 'is_active', 'is_public'
    ]
    list_filter = [
        'workspace', 'is_active', 'is_public', 'is_recurring'
    ]
    search_fields = ['name', 'description', 'workspace__name']
    readonly_fields = ['id', 'usage_count', 'created_at', 'updated_at', 'created_by']
    ordering = ['workspace', 'name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('workspace', 'name', 'description')
        }),
        (_('Template Data'), {
            'fields': ('template_data',),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('is_recurring', 'recurrence_pattern', 'default_duration_minutes',
                      'auto_include_entries', 'include_rules')
        }),
        (_('Usage'), {
            'fields': ('usage_count', 'is_active', 'is_public')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


# Inline admin classes for related models
class TimesheetEntryInline(admin.TabularInline):
    """Inline admin for TimesheetEntry model."""
    model = TimesheetEntry
    extra = 0
    fields = ['time_entry', 'notes', 'adjusted_hours', 'adjusted_rate']
    readonly_fields = ['get_effective_hours', 'get_effective_rate']
    show_change_view = True


class TimesheetCommentInline(admin.TabularInline):
    """Inline admin for TimesheetComment model."""
    model = TimesheetComment
    extra = 0
    fields = ['author', 'content', 'comment_type', 'is_private']
    readonly_fields = ['created_at']
    show_change_view = True


# Add inlines to related models
TimesheetAdmin.inlines = [TimesheetEntryInline, TimesheetCommentInline]