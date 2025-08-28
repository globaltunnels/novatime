"""
Admin configuration for tasks app.

This module configures the Django admin interface for task-related models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta


from .models import (
    Project, Task, Assignment, Epic, Sprint, Dependency,
    Template, Comment, Attachment, Tag
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for Project model."""

    list_display = [
        'name', 'organization', 'workspace', 'status', 'progress_percentage',
        'team_members_count', 'tasks_count', 'created_at'
    ]
    list_filter = [
        'organization', 'workspace', 'status', 'priority', 'created_at'
    ]
    search_fields = [
        'name', 'organization__name', 'workspace__name', 'owner__email'
    ]
    readonly_fields = [
        'id', 'slug', 'progress_percentage', 'team_members_count', 'tasks_count',
        'completed_tasks_count', 'overdue_tasks_count', 'total_estimated_hours',
        'total_logged_hours', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Project'), {
            'fields': ('organization', 'workspace', 'name', 'slug', 'description')
        }),
        (_('Details'), {
            'fields': ('project_type', 'methodology', 'status', 'priority')
        }),
        (_('Timeline'), {
            'fields': ('start_date', 'end_date', 'actual_end_date')
        }),
        (_('Budget & Estimates'), {
            'fields': ('budget', 'estimated_hours', 'actual_hours')
        }),
        (_('Settings'), {
            'fields': ('is_private', 'allow_guest_access', 'require_time_tracking')
        }),
        (_('Ownership'), {
            'fields': ('created_by', 'owner')
        }),
        (_('Statistics'), {
            'fields': ('progress_percentage', 'team_members_count', 'tasks_count',
                      'completed_tasks_count', 'overdue_tasks_count',
                      'total_estimated_hours', 'total_logged_hours'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def team_members_count(self, obj):
        """Display team members count."""
        return obj.get_team_members_count()
    team_members_count.short_description = _('Team Members')

    def tasks_count(self, obj):
        """Display tasks count."""
        return obj.get_tasks_count()
    tasks_count.short_description = _('Tasks')

    def completed_tasks_count(self, obj):
        """Display completed tasks count."""
        return obj.get_completed_tasks_count()
    completed_tasks_count.short_description = _('Completed')

    def overdue_tasks_count(self, obj):
        """Display overdue tasks count."""
        return obj.get_overdue_tasks_count()
    overdue_tasks_count.short_description = _('Overdue')

    def total_estimated_hours(self, obj):
        """Display total estimated hours."""
        return f"{obj.get_total_estimated_hours():.1f}h"
    total_estimated_hours.short_description = _('Est. Hours')

    def total_logged_hours(self, obj):
        """Display total logged hours."""
        return f"{obj.get_total_logged_hours():.1f}h"
    total_logged_hours.short_description = _('Logged Hours')

    actions = ['activate_projects', 'complete_projects', 'archive_projects']

    def activate_projects(self, request, queryset):
        """Activate selected projects."""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            ngettext(
                '%d project was successfully activated.',
                '%d projects were successfully activated.',
                updated,
            ) % updated,
        )
    activate_projects.short_description = _('Activate selected projects')

    def complete_projects(self, request, queryset):
        """Complete selected projects."""
        updated = queryset.update(status='completed')
        self.message_user(
            request,
            ngettext(
                '%d project was successfully completed.',
                '%d projects were successfully completed.',
                updated,
            ) % updated,
        )
    complete_projects.short_description = _('Complete selected projects')

    def archive_projects(self, request, queryset):
        """Archive selected projects."""
        updated = queryset.update(status='cancelled')
        self.message_user(
            request,
            ngettext(
                '%d project was successfully archived.',
                '%d projects were successfully archived.',
                updated,
            ) % updated,
        )
    archive_projects.short_description = _('Archive selected projects')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin for Task model."""

    list_display = [
        'title', 'project', 'status', 'priority', 'assignee', 'due_date',
        'estimated_hours', 'progress_percentage', 'created_at'
    ]
    list_filter = [
        'project', 'status', 'priority', 'assignee', 'due_date', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'project__name', 'assignee__email'
    ]
    readonly_fields = [
        'id', 'actual_hours', 'progress_percentage', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Task'), {
            'fields': ('project', 'title', 'description')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        (_('Assignment'), {
            'fields': ('assignee', 'reporter')
        }),
        (_('Timeline'), {
            'fields': ('due_date', 'completed_at')
        }),
        (_('Estimates'), {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        (_('Organization'), {
            'fields': ('epic', 'sprint', 'parent_task')
        }),
        (_('Tags & Fields'), {
            'fields': ('labels', 'custom_fields'),
            'classes': ('collapse',)
        }),
        (_('Ownership'), {
            'fields': ('created_by',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_completed', 'mark_in_progress', 'mark_blocked', 'update_priority']

    def mark_completed(self, request, queryset):
        """Mark selected tasks as completed."""
        updated = queryset.update(status='done', completed_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                '%d task was successfully completed.',
                '%d tasks were successfully completed.',
                updated,
            ) % updated,
        )
    mark_completed.short_description = _('Mark selected tasks as completed')

    def mark_in_progress(self, request, queryset):
        """Mark selected tasks as in progress."""
        updated = queryset.update(status='in_progress')
        self.message_user(
            request,
            ngettext(
                '%d task was successfully marked as in progress.',
                '%d tasks were successfully marked as in progress.',
                updated,
            ) % updated,
        )
    mark_in_progress.short_description = _('Mark selected tasks as in progress')

    def mark_blocked(self, request, queryset):
        """Mark selected tasks as blocked."""
        updated = queryset.update(status='blocked')
        self.message_user(
            request,
            ngettext(
                '%d task was successfully marked as blocked.',
                '%d tasks were successfully marked as blocked.',
                updated,
            ) % updated,
        )
    mark_blocked.short_description = _('Mark selected tasks as blocked')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin for Assignment model."""

    list_display = [
        'user', 'project', 'task', 'role', 'load_percentage', 'is_active', 'created_at'
    ]
    list_filter = [
        'project', 'role', 'is_active', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 'project__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['project', 'user']

    fieldsets = (
        (_('Assignment'), {
            'fields': ('project', 'user', 'task')
        }),
        (_('Details'), {
            'fields': ('role', 'load_percentage')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Epic)
class EpicAdmin(admin.ModelAdmin):
    """Admin for Epic model."""

    list_display = [
        'name', 'project', 'status', 'priority', 'progress_percentage',
        'estimated_hours', 'created_at'
    ]
    list_filter = [
        'project', 'status', 'priority', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'project__name'
    ]
    readonly_fields = [
        'id', 'progress_percentage', 'created_at', 'updated_at'
    ]
    ordering = ['project', 'name']

    fieldsets = (
        (_('Epic'), {
            'fields': ('project', 'name', 'description')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        (_('Estimates'), {
            'fields': ('estimated_hours',)
        }),
        (_('Ownership'), {
            'fields': ('created_by',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    """Admin for Sprint model."""

    list_display = [
        'name', 'project', 'status', 'start_date', 'end_date',
        'planned_capacity', 'actual_capacity', 'created_at'
    ]
    list_filter = [
        'project', 'status', 'start_date', 'created_at'
    ]
    search_fields = [
        'name', 'goal', 'project__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['project', '-start_date']

    fieldsets = (
        (_('Sprint'), {
            'fields': ('project', 'name', 'goal')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Capacity'), {
            'fields': ('planned_capacity', 'actual_capacity')
        }),
        (_('Ownership'), {
            'fields': ('created_by',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Dependency)
class DependencyAdmin(admin.ModelAdmin):
    """Admin for Dependency model."""

    list_display = [
        'blocking_task', 'dependent_task', 'dependency_type', 'lag_days', 'created_at'
    ]
    list_filter = [
        'project', 'dependency_type', 'created_at'
    ]
    search_fields = [
        'blocking_task__title', 'dependent_task__title', 'project__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['project', 'blocking_task']

    fieldsets = (
        (_('Dependency'), {
            'fields': ('project', 'blocking_task', 'dependent_task')
        }),
        (_('Details'), {
            'fields': ('dependency_type', 'lag_days')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Admin for Template model."""

    list_display = [
        'name', 'template_type', 'organization', 'is_public', 'usage_count', 'created_at'
    ]
    list_filter = [
        'template_type', 'organization', 'is_public', 'created_at'
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
            'fields': ('organization', 'created_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for Comment model."""

    list_display = [
        'task', 'author', 'content_preview', 'created_at'
    ]
    list_filter = [
        'task', 'author', 'created_at'
    ]
    search_fields = [
        'content', 'task__title', 'author__email'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Comment'), {
            'fields': ('task', 'author', 'content')
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


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Admin for Attachment model."""

    list_display = [
        'task', 'filename', 'uploaded_by', 'file_size', 'created_at'
    ]
    list_filter = [
        'task', 'uploaded_by', 'created_at'
    ]
    search_fields = [
        'filename', 'task__title', 'uploaded_by__email'
    ]
    readonly_fields = [
        'id', 'file_url', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (_('Attachment'), {
            'fields': ('task', 'uploaded_by', 'file', 'filename')
        }),
        (_('File Info'), {
            'fields': ('file_size', 'content_type', 'file_url')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""

    list_display = [
        'name', 'organization', 'usage_count', 'created_at'
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


# Inline admin classes
class TaskInline(admin.TabularInline):
    """Inline admin for Task model."""
    model = Task
    extra = 0
    fields = ['title', 'status', 'priority', 'assignee', 'due_date']
    readonly_fields = ['created_at']
    show_change_view = True


class AssignmentInline(admin.TabularInline):
    """Inline admin for Assignment model."""
    model = Assignment
    extra = 0
    fields = ['user', 'role', 'load_percentage', 'is_active']
    show_change_view = True


class EpicInline(admin.TabularInline):
    """Inline admin for Epic model."""
    model = Epic
    extra = 0
    fields = ['name', 'status', 'priority', 'progress_percentage']
    readonly_fields = ['progress_percentage']
    show_change_view = True


class SprintInline(admin.TabularInline):
    """Inline admin for Sprint model."""
    model = Sprint
    extra = 0
    fields = ['name', 'status', 'start_date', 'end_date']
    show_change_view = True


class CommentInline(admin.TabularInline):
    """Inline admin for Comment model."""
    model = Comment
    extra = 0
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']
    show_change_view = True


class AttachmentInline(admin.TabularInline):
    """Inline admin for Attachment model."""
    model = Attachment
    extra = 0
    fields = ['filename', 'uploaded_by', 'file_size', 'created_at']
    readonly_fields = ['file_size', 'created_at']
    show_change_view = True


# Add inlines to Project admin
ProjectAdmin.inlines = [
    AssignmentInline,
    EpicInline,
    SprintInline,
    TaskInline
]

# Add inlines to Task admin
TaskAdmin.inlines = [
    CommentInline,
    AttachmentInline
]