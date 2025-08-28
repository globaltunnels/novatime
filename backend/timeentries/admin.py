"""
Admin configuration for time_entries app.

This module configures the Django admin interface for time entry-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta


from .models import (
    TimeEntry, Timer, TimeEntryApproval, IdlePeriod, TimeEntryTemplate,
    TimeEntryCategory, TimeEntryTag, TimeEntryComment, TimeEntryAttachment
)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    """Admin for TimeEntry model."""

    list_display = [
        'user', 'project', 'task', 'start_time', 'duration_minutes',
        'status', 'is_billable', 'cost_amount', 'created_at'
    ]
    list_filter = [
        'organization', 'workspace', 'project', 'task', 'status',
        'entry_type', 'is_billable', 'start_time', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'project__name', 'task__title', 'description'
    ]
    readonly_fields = [
        'id', 'cost_amount', 'created_at', 'updated_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Time Entry'), {
            'fields': ('organization', 'workspace', 'user', 'project', 'task')
        }),
        (_('Time Details'), {
            'fields': ('start_time', 'end_time', 'duration_minutes', 'entry_type')
        }),
        (_('Description & Billing'), {
            'fields': ('description', 'is_billable', 'hourly_rate', 'cost_amount')
        }),
        (_('Status & Approval'), {
            'fields': ('status', 'submitted_at', 'approved_at', 'approved_by', 'rejection_reason')
        }),
        (_('Location & Context'), {
            'fields': ('location', 'ip_address', 'user_agent')
        }),
        (_('Tags & Categories'), {
            'fields': ('tags', 'categories', 'custom_fields'),
            'classes': ('collapse',)
        }),
        (_('Integration'), {
            'fields': ('integration_data',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['submit_entries', 'approve_entries', 'reject_entries', 'lock_entries']

    def submit_entries(self, request, queryset):
        """Submit selected time entries for approval."""
        updated = queryset.update(status='submitted', submitted_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                '%d time entry was successfully submitted.',
                '%d time entries were successfully submitted.',
                updated,
            ) % updated,
        )
    submit_entries.short_description = _('Submit selected entries for approval')

    def approve_entries(self, request, queryset):
        """Approve selected time entries."""
        updated = queryset.update(
            status='approved',
            approved_at=timezone.now(),
            approved_by=request.user
        )
        self.message_user(
            request,
            ngettext(
                '%d time entry was successfully approved.',
                '%d time entries were successfully approved.',
                updated,
            ) % updated,
        )
    approve_entries.short_description = _('Approve selected entries')

    def reject_entries(self, request, queryset):
        """Reject selected time entries."""
        updated = queryset.update(status='rejected')
        self.message_user(
            request,
            ngettext(
                '%d time entry was successfully rejected.',
                '%d time entries were successfully rejected.',
                updated,
            ) % updated,
        )
    reject_entries.short_description = _('Reject selected entries')

    def lock_entries(self, request, queryset):
        """Lock selected time entries."""
        updated = queryset.update(status='locked')
        self.message_user(
            request,
            ngettext(
                '%d time entry was successfully locked.',
                '%d time entries were successfully locked.',
                updated,
            ) % updated,
        )
    lock_entries.short_description = _('Lock selected entries')


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    """Admin for Timer model."""

    list_display = [
        'user', 'project', 'task', 'status', 'start_time', 'elapsed_time',
        'is_idle', 'created_at'
    ]
    list_filter = [
        'organization', 'workspace', 'project', 'task', 'status', 'start_time', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'project__name', 'task__title', 'description'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Timer'), {
            'fields': ('organization', 'workspace', 'user', 'project', 'task')
        }),
        (_('Timing'), {
            'fields': ('start_time', 'end_time', 'paused_at', 'total_paused_seconds')
        }),
        (_('Status & Settings'), {
            'fields': ('status', 'is_billable', 'hourly_rate', 'idle_threshold_minutes')
        }),
        (_('Activity'), {
            'fields': ('last_activity_at', 'location', 'ip_address')
        }),
        (_('Description'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['start_timers', 'pause_timers', 'stop_timers']

    def start_timers(self, request, queryset):
        """Start selected timers."""
        updated = 0
        for timer in queryset:
            if timer.status == 'stopped':
                timer.start()
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d timer was successfully started.',
                '%d timers were successfully started.',
                updated,
            ) % updated,
        )
    start_timers.short_description = _('Start selected timers')

    def pause_timers(self, request, queryset):
        """Pause selected timers."""
        updated = 0
        for timer in queryset:
            if timer.status == 'running':
                timer.pause()
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d timer was successfully paused.',
                '%d timers were successfully paused.',
                updated,
            ) % updated,
        )
    pause_timers.short_description = _('Pause selected timers')

    def stop_timers(self, request, queryset):
        """Stop selected timers."""
        updated = 0
        for timer in queryset:
            if timer.status in ['running', 'paused']:
                timer.stop()
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d timer was successfully stopped.',
                '%d timers were successfully stopped.',
                updated,
            ) % updated,
        )
    stop_timers.short_description = _('Stop selected timers')


@admin.register(TimeEntryApproval)
class TimeEntryApprovalAdmin(admin.ModelAdmin):
    """Admin for TimeEntryApproval model."""

    list_display = [
        'requested_by', 'approver', 'organization', 'period_start', 'period_end',
        'status', 'total_hours', 'total_entries', 'requested_at'
    ]
    list_filter = [
        'organization', 'workspace', 'approver', 'requested_by', 'status',
        'approval_type', 'requested_at'
    ]
    search_fields = [
        'requested_by__email', 'approver__email', 'organization__name'
    ]
    readonly_fields = [
        'id', 'total_hours', 'billable_hours', 'total_entries', 'requested_at',
        'responded_at', 'created_at', 'updated_at'
    ]
    ordering = ['-requested_at']

    fieldsets = (
        (_('Approval Request'), {
            'fields': ('organization', 'workspace', 'approver', 'requested_by')
        }),
        (_('Time Period'), {
            'fields': ('approval_type', 'period_start', 'period_end')
        }),
        (_('Status'), {
            'fields': ('status', 'requested_at', 'responded_at')
        }),
        (_('Comments'), {
            'fields': ('approver_comments', 'requested_notes')
        }),
        (_('Time Entries'), {
            'fields': ('time_entries',),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('total_hours', 'billable_hours', 'total_entries'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """Approve selected approval requests."""
        updated = 0
        for approval in queryset:
            if approval.status == 'pending':
                approval.approve('Approved via admin')
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d approval request was successfully approved.',
                '%d approval requests were successfully approved.',
                updated,
            ) % updated,
        )
    approve_requests.short_description = _('Approve selected requests')

    def reject_requests(self, request, queryset):
        """Reject selected approval requests."""
        updated = 0
        for approval in queryset:
            if approval.status == 'pending':
                approval.reject('Rejected via admin')
                updated += 1
        self.message_user(
            request,
            ngettext(
                '%d approval request was successfully rejected.',
                '%d approval requests were successfully rejected.',
                updated,
            ) % updated,
        )
    reject_requests.short_description = _('Reject selected requests')


@admin.register(IdlePeriod)
class IdlePeriodAdmin(admin.ModelAdmin):
    """Admin for IdlePeriod model."""

    list_display = [
        'user', 'timer', 'start_time', 'duration_seconds', 'reason',
        'action_taken', 'created_at'
    ]
    list_filter = [
        'user', 'timer', 'reason', 'action_taken', 'start_time', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'id', 'duration_seconds', 'created_at', 'updated_at'
    ]
    ordering = ['-start_time']

    fieldsets = (
        (_('Idle Period'), {
            'fields': ('user', 'timer', 'start_time', 'end_time')
        }),
        (_('Details'), {
            'fields': ('duration_seconds', 'reason', 'context_data')
        }),
        (_('Action'), {
            'fields': ('action_taken',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntryTemplate)
class TimeEntryTemplateAdmin(admin.ModelAdmin):
    """Admin for TimeEntryTemplate model."""

    list_display = [
        'name', 'organization', 'template_type', 'is_public', 'usage_count',
        'created_by', 'created_at'
    ]
    list_filter = [
        'organization', 'template_type', 'is_public', 'is_system', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'organization__name'
    ]
    readonly_fields = [
        'id', 'usage_count', 'created_at', 'updated_at'
    ]
    ordering = ['-usage_count', 'name']

    fieldsets = (
        (_('Template'), {
            'fields': ('name', 'description', 'template_type')
        }),
        (_('Data'), {
            'fields': ('template_data',),
            'classes': ('collapse',)
        }),
        (_('Visibility'), {
            'fields': ('is_public', 'is_system')
        }),
        (_('Usage'), {
            'fields': ('usage_count',)
        }),
        (_('Organization'), {
            'fields': ('organization', 'workspace', 'created_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntryCategory)
class TimeEntryCategoryAdmin(admin.ModelAdmin):
    """Admin for TimeEntryCategory model."""

    list_display = [
        'name', 'organization', 'usage_count', 'created_by', 'created_at'
    ]
    list_filter = [
        'organization', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'organization__name'
    ]
    readonly_fields = [
        'id', 'usage_count', 'created_at', 'updated_at'
    ]
    ordering = ['name']

    fieldsets = (
        (_('Category'), {
            'fields': ('name', 'description', 'color', 'icon')
        }),
        (_('Usage'), {
            'fields': ('usage_count',)
        }),
        (_('Organization'), {
            'fields': ('organization', 'created_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntryTag)
class TimeEntryTagAdmin(admin.ModelAdmin):
    """Admin for TimeEntryTag model."""

    list_display = [
        'name', 'organization', 'usage_count', 'created_by', 'created_at'
    ]
    list_filter = [
        'organization', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'organization__name'
    ]
    readonly_fields = [
        'id', 'usage_count', 'created_at', 'updated_at'
    ]
    ordering = ['name']

    fieldsets = (
        (_('Tag'), {
            'fields': ('name', 'description', 'color')
        }),
        (_('Usage'), {
            'fields': ('usage_count',)
        }),
        (_('Organization'), {
            'fields': ('organization', 'created_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntryComment)
class TimeEntryCommentAdmin(admin.ModelAdmin):
    """Admin for TimeEntryComment model."""

    list_display = [
        'time_entry', 'author', 'content_preview', 'created_at'
    ]
    list_filter = [
        'time_entry', 'author', 'created_at'
    ]
    search_fields = [
        'content', 'time_entry__description', 'author__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Comment'), {
            'fields': ('time_entry', 'author', 'content')
        }),
        (_('Threading'), {
            'fields': ('parent_comment',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Display content preview."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('Content')


@admin.register(TimeEntryAttachment)
class TimeEntryAttachmentAdmin(admin.ModelAdmin):
    """Admin for TimeEntryAttachment model."""

    list_display = [
        'time_entry', 'filename', 'uploaded_by', 'file_size', 'created_at'
    ]
    list_filter = [
        'time_entry', 'uploaded_by', 'created_at'
    ]
    search_fields = [
        'filename', 'time_entry__description', 'uploaded_by__email'
    ]
    readonly_fields = [
        'id', 'file_url', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Attachment'), {
            'fields': ('time_entry', 'uploaded_by', 'file', 'filename')
        }),
        (_('File Info'), {
            'fields': ('file_size', 'content_type', 'file_url')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Inline admin classes
class TimeEntryInline(admin.TabularInline):
    """Inline admin for TimeEntry model."""
    model = TimeEntry
    extra = 0
    fields = ['user', 'start_time', 'duration_minutes', 'status', 'is_billable']
    readonly_fields = ['created_at']
    show_change_view = True


class TimerInline(admin.TabularInline):
    """Inline admin for Timer model."""
    model = Timer
    extra = 0
    fields = ['user', 'status', 'start_time', 'is_billable']
    readonly_fields = ['created_at']
    show_change_view = True


class TimeEntryCommentInline(admin.TabularInline):
    """Inline admin for TimeEntryComment model."""
    model = TimeEntryComment
    extra = 0
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


class TimeEntryAttachmentInline(admin.TabularInline):
    """Inline admin for TimeEntryAttachment model."""
    model = TimeEntryAttachment
    extra = 0
    fields = ['filename', 'uploaded_by', 'file_size', 'created_at']
    readonly_fields = ['file_size', 'created_at']
    show_change_view = True


# Add inlines to TimeEntry admin
TimeEntryAdmin.inlines = [
    TimeEntryCommentInline,
    TimeEntryAttachmentInline
]