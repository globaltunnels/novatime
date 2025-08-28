"""
Serializers for tasks app.

This module contains serializers for Project, Task, Assignment, Epic, Sprint,
Dependency, Template, Comment, Attachment, Tag, and related models for API
serialization and validation.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, fields
from decimal import Decimal

from .models import (
    Project, Task, Assignment, Epic, Sprint, Dependency,
    Template, Comment, Attachment, Tag
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'description', 'color', 'usage_count',
            'organization', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']

    def get_usage_count(self, obj):
        """Get usage count."""
        return obj.usage_count


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Attachment model."""

    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = Attachment
        fields = [
            'id', 'task', 'uploaded_by', 'uploaded_by_name', 'file', 'file_url',
            'filename', 'file_size', 'content_type', 'created_at'
        ]
        read_only_fields = ['id', 'file_url', 'created_at']

    def get_file_url(self, obj):
        """Get file URL."""
        if obj.file:
            return obj.file.url
        return None


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""

    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )
    replies_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'task', 'author', 'author_name', 'content', 'parent_comment',
            'replies_count', 'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'replies_count', 'replies', 'created_at', 'updated_at']

    def get_replies_count(self, obj):
        """Get replies count."""
        return obj.replies.count()

    def get_replies(self, obj):
        """Get replies."""
        if self.context.get('include_replies', False):
            replies = obj.get_replies()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []


class DependencySerializer(serializers.ModelSerializer):
    """Serializer for Dependency model."""

    blocking_task_title = serializers.CharField(
        source='blocking_task.title',
        read_only=True
    )
    dependent_task_title = serializers.CharField(
        source='dependent_task.title',
        read_only=True
    )

    class Meta:
        model = Dependency
        fields = [
            'id', 'project', 'blocking_task', 'blocking_task_title',
            'dependent_task', 'dependent_task_title', 'dependency_type',
            'lag_days', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model."""

    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'template_type', 'template_data',
            'is_public', 'is_system', 'usage_count', 'organization',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class SprintSerializer(serializers.ModelSerializer):
    """Serializer for Sprint model."""

    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    remaining_capacity = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = [
            'id', 'name', 'goal', 'project', 'start_date', 'end_date', 'status',
            'planned_capacity', 'actual_capacity', 'tasks_count',
            'completed_tasks_count', 'progress_percentage', 'remaining_capacity',
            'is_overdue', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tasks_count', 'completed_tasks_count', 'progress_percentage',
            'remaining_capacity', 'is_overdue', 'created_at', 'updated_at'
        ]

    def get_tasks_count(self, obj):
        """Get tasks count."""
        return obj.get_tasks_count()

    def get_completed_tasks_count(self, obj):
        """Get completed tasks count."""
        return obj.get_completed_tasks_count()

    def get_progress_percentage(self, obj):
        """Get progress percentage."""
        total = obj.get_tasks_count()
        if total > 0:
            return int((obj.get_completed_tasks_count() / total) * 100)
        return 0

    def get_remaining_capacity(self, obj):
        """Get remaining capacity."""
        return obj.get_remaining_capacity()

    def get_is_overdue(self, obj):
        """Check if overdue."""
        return obj.is_overdue()


class EpicSerializer(serializers.ModelSerializer):
    """Serializer for Epic model."""

    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Epic
        fields = [
            'id', 'name', 'description', 'project', 'status', 'priority',
            'progress_percentage', 'estimated_hours', 'tasks_count',
            'completed_tasks_count', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'progress_percentage', 'tasks_count', 'completed_tasks_count',
            'created_at', 'updated_at'
        ]

    def get_tasks_count(self, obj):
        """Get tasks count."""
        return obj.tasks.count()

    def get_completed_tasks_count(self, obj):
        """Get completed tasks count."""
        return obj.tasks.filter(status='done').count()

    def get_progress_percentage(self, obj):
        """Get progress percentage."""
        return obj.progress_percentage


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model."""

    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    user_email = serializers.CharField(
        source='user.email',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.title',
        read_only=True
    )

    class Meta:
        model = Assignment
        fields = [
            'id', 'project', 'project_name', 'user', 'user_name', 'user_email',
            'task', 'task_title', 'role', 'load_percentage', 'start_date',
            'end_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""

    assignee_name = serializers.CharField(
        source='assignee.get_full_name',
        read_only=True
    )
    reporter_name = serializers.CharField(
        source='reporter.get_full_name',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    epic_name = serializers.CharField(
        source='epic.name',
        read_only=True
    )
    sprint_name = serializers.CharField(
        source='sprint.name',
        read_only=True
    )
    parent_task_title = serializers.CharField(
        source='parent_task.title',
        read_only=True
    )

    # Computed fields
    logged_hours = serializers.SerializerMethodField()
    remaining_hours = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    blocking_tasks_count = serializers.SerializerMethodField()
    blocked_tasks_count = serializers.SerializerMethodField()
    subtasks_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    attachments_count = serializers.SerializerMethodField()

    # Related data
    assignments = AssignmentSerializer(many=True, read_only=True)
    dependencies = DependencySerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'project',
            'project_name', 'epic', 'epic_name', 'sprint', 'sprint_name',
            'parent_task', 'parent_task_title', 'assignee', 'assignee_name',
            'reporter', 'reporter_name', 'due_date', 'completed_at',
            'estimated_hours', 'actual_hours', 'progress_percentage',
            'labels', 'custom_fields', 'created_by', 'logged_hours',
            'remaining_hours', 'is_overdue', 'blocking_tasks_count',
            'blocked_tasks_count', 'subtasks_count', 'comments_count',
            'attachments_count', 'assignments', 'dependencies', 'comments',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'actual_hours', 'logged_hours', 'remaining_hours', 'is_overdue',
            'blocking_tasks_count', 'blocked_tasks_count', 'subtasks_count',
            'comments_count', 'attachments_count', 'assignments', 'dependencies',
            'comments', 'attachments', 'created_at', 'updated_at'
        ]

    def get_logged_hours(self, obj):
        """Get logged hours."""
        return obj.get_logged_hours() / 60  # Convert minutes to hours

    def get_remaining_hours(self, obj):
        """Get remaining hours."""
        return obj.get_remaining_hours()

    def get_is_overdue(self, obj):
        """Check if overdue."""
        return obj.is_overdue()

    def get_blocking_tasks_count(self, obj):
        """Get blocking tasks count."""
        return obj.get_blocking_tasks().count()

    def get_blocked_tasks_count(self, obj):
        """Get blocked tasks count."""
        return obj.get_blocked_tasks().count()

    def get_subtasks_count(self, obj):
        """Get subtasks count."""
        return obj.subtasks.count()

    def get_comments_count(self, obj):
        """Get comments count."""
        return obj.comments.count()

    def get_attachments_count(self, obj):
        """Get attachments count."""
        return obj.attachments.count()


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks."""

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'project', 'epic', 'sprint',
            'parent_task', 'assignee', 'reporter', 'due_date', 'estimated_hours',
            'labels', 'custom_fields'
        ]

    def validate_project(self, value):
        """Validate project access."""
        user = self.context['request'].user
        if not value.can_user_access(user):
            raise serializers.ValidationError(
                _("You don't have access to this project.")
            )
        return value

    def validate_assignee(self, value):
        """Validate assignee access."""
        if value:
            project = self.validated_data.get('project')
            if project and not project.can_user_access(value):
                raise serializers.ValidationError(
                    _("Assignee doesn't have access to this project.")
                )
        return value

    def create(self, validated_data):
        """Create task."""
        validated_data['created_by'] = self.context['request'].user
        if 'reporter' not in validated_data:
            validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    owner_name = serializers.CharField(
        source='owner.get_full_name',
        read_only=True
    )
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    workspace_name = serializers.CharField(
        source='workspace.name',
        read_only=True
    )

    # Statistics
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    overdue_tasks_count = serializers.SerializerMethodField()
    team_members_count = serializers.SerializerMethodField()
    total_estimated_hours = serializers.SerializerMethodField()
    total_logged_hours = serializers.SerializerMethodField()
    budget_utilization = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    is_on_track = serializers.SerializerMethodField()

    # Related data
    epics = EpicSerializer(many=True, read_only=True)
    sprints = SprintSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'slug', 'description', 'project_type', 'methodology',
            'status', 'priority', 'progress_percentage', 'start_date', 'end_date',
            'actual_end_date', 'budget', 'estimated_hours', 'actual_hours',
            'organization', 'organization_name', 'workspace', 'workspace_name',
            'created_by', 'created_by_name', 'owner', 'owner_name', 'is_private',
            'allow_guest_access', 'require_time_tracking', 'tasks_count',
            'completed_tasks_count', 'overdue_tasks_count', 'team_members_count',
            'total_estimated_hours', 'total_logged_hours', 'budget_utilization',
            'is_overdue', 'is_on_track', 'epics', 'sprints', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'progress_percentage', 'actual_hours', 'tasks_count',
            'completed_tasks_count', 'overdue_tasks_count', 'team_members_count',
            'total_estimated_hours', 'total_logged_hours', 'budget_utilization',
            'is_overdue', 'is_on_track', 'epics', 'sprints', 'created_at', 'updated_at'
        ]

    def get_tasks_count(self, obj):
        """Get tasks count."""
        return obj.get_tasks_count()

    def get_completed_tasks_count(self, obj):
        """Get completed tasks count."""
        return obj.get_completed_tasks_count()

    def get_overdue_tasks_count(self, obj):
        """Get overdue tasks count."""
        return obj.get_overdue_tasks_count()

    def get_team_members_count(self, obj):
        """Get team members count."""
        return obj.get_team_members_count()

    def get_total_estimated_hours(self, obj):
        """Get total estimated hours."""
        return obj.get_total_estimated_hours()

    def get_total_logged_hours(self, obj):
        """Get total logged hours."""
        return obj.get_total_logged_hours() / 60  # Convert minutes to hours

    def get_budget_utilization(self, obj):
        """Get budget utilization."""
        return obj.get_budget_utilization()

    def get_is_overdue(self, obj):
        """Check if overdue."""
        return obj.is_overdue()

    def get_is_on_track(self, obj):
        """Check if on track."""
        return obj.is_on_track()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""

    class Meta:
        model = Project
        fields = [
            'name', 'description', 'project_type', 'methodology', 'priority',
            'start_date', 'end_date', 'budget', 'estimated_hours', 'organization',
            'workspace', 'is_private', 'allow_guest_access', 'require_time_tracking'
        ]

    def validate_organization(self, value):
        """Validate organization access."""
        user = self.context['request'].user
        if not value.users.filter(id=user.id).exists():
            raise serializers.ValidationError(
                _("You don't have access to this organization.")
            )
        return value

    def validate_workspace(self, value):
        """Validate workspace access."""
        user = self.context['request'].user
        if not value.memberships.filter(user=user, is_active=True).exists():
            raise serializers.ValidationError(
                _("You don't have access to this workspace.")
            )
        return value

    def create(self, validated_data):
        """Create project."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics."""

    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    todo_tasks = serializers.IntegerField()
    blocked_tasks = serializers.IntegerField()
    total_team_members = serializers.IntegerField()
    active_team_members = serializers.IntegerField()
    total_estimated_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    total_logged_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    average_hours_per_task = serializers.DecimalField(max_digits=6, decimal_places=2)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overdue_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    budget_utilization = serializers.DecimalField(max_digits=5, decimal_places=2)
    velocity = serializers.DecimalField(max_digits=6, decimal_places=2)
    burndown_data = serializers.ListField()
    team_performance = serializers.ListField()


class TaskBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk task actions."""

    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of task IDs to act upon')
    )

    action = serializers.ChoiceField(
        choices=[
            'update_status', 'update_priority', 'update_assignee',
            'update_due_date', 'add_labels', 'remove_labels', 'delete'
        ],
        help_text=_('Action to perform on the tasks')
    )

    status = serializers.ChoiceField(
        choices=['todo', 'in_progress', 'review', 'done', 'blocked'],
        required=False,
        help_text=_('New status (for update_status action)')
    )

    priority = serializers.ChoiceField(
        choices=['lowest', 'low', 'medium', 'high', 'highest'],
        required=False,
        help_text=_('New priority (for update_priority action)')
    )

    assignee_id = serializers.UUIDField(
        required=False,
        help_text=_('New assignee ID (for update_assignee action)')
    )

    due_date = serializers.DateField(
        required=False,
        help_text=_('New due date (for update_due_date action)')
    )

    labels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('Labels to add/remove')
    )

    def validate(self, data):
        """Validate bulk action data."""
        action = data.get('action')

        if action == 'update_status' and 'status' not in data:
            raise serializers.ValidationError(
                _("Status is required for update_status action.")
            )

        if action == 'update_priority' and 'priority' not in data:
            raise serializers.ValidationError(
                _("Priority is required for update_priority action.")
            )

        if action == 'update_assignee' and 'assignee_id' not in data:
            raise serializers.ValidationError(
                _("Assignee ID is required for update_assignee action.")
            )

        if action == 'update_due_date' and 'due_date' not in data:
            raise serializers.ValidationError(
                _("Due date is required for update_due_date action.")
            )

        return data


class ProjectTemplateSerializer(serializers.Serializer):
    """Serializer for project templates."""

    name = serializers.CharField(help_text=_('Template name'))
    description = serializers.CharField(required=False, help_text=_('Template description'))
    include_tasks = serializers.BooleanField(default=True, help_text=_('Include tasks in template'))
    include_epics = serializers.BooleanField(default=True, help_text=_('Include epics in template'))
    include_sprints = serializers.BooleanField(default=True, help_text=_('Include sprints in template'))
    include_dependencies = serializers.BooleanField(default=True, help_text=_('Include dependencies in template'))
    include_assignments = serializers.BooleanField(default=True, help_text=_('Include assignments in template'))


class TaskTemplateSerializer(serializers.Serializer):
    """Serializer for task templates."""

    name = serializers.CharField(help_text=_('Template name'))
    description = serializers.CharField(required=False, help_text=_('Template description'))
    include_subtasks = serializers.BooleanField(default=True, help_text=_('Include subtasks in template'))
    include_comments = serializers.BooleanField(default=False, help_text=_('Include comments in template'))
    include_attachments = serializers.BooleanField(default=False, help_text=_('Include attachments in template'))
    include_dependencies = serializers.BooleanField(default=True, help_text=_('Include dependencies in template'))


class ProjectImportSerializer(serializers.Serializer):
    """Serializer for project import."""

    template_id = serializers.UUIDField(help_text=_('Template ID to import from'))
    name = serializers.CharField(help_text=_('New project name'))
    workspace_id = serializers.UUIDField(help_text=_('Workspace ID for the new project'))
    start_date = serializers.DateField(required=False, help_text=_('Project start date'))
    end_date = serializers.DateField(required=False, help_text=_('Project end date'))
    assignee_mapping = serializers.DictField(
        required=False,
        help_text=_('Mapping of old user IDs to new user IDs')
    )


class TaskMoveSerializer(serializers.Serializer):
    """Serializer for moving tasks between projects/epics/sprints."""

    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of task IDs to move')
    )

    project_id = serializers.UUIDField(
        required=False,
        help_text=_('New project ID')
    )

    epic_id = serializers.UUIDField(
        required=False,
        help_text=_('New epic ID')
    )

    sprint_id = serializers.UUIDField(
        required=False,
        help_text=_('New sprint ID')
    )

    def validate(self, data):
        """Validate move data."""
        if not any([data.get('project_id'), data.get('epic_id'), data.get('sprint_id')]):
            raise serializers.ValidationError(
                _("At least one of project_id, epic_id, or sprint_id must be provided.")
            )

        return data


class TaskCloneSerializer(serializers.Serializer):
    """Serializer for cloning tasks."""

    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_('List of task IDs to clone')
    )

    project_id = serializers.UUIDField(
        required=False,
        help_text=_('Project ID for cloned tasks')
    )

    include_subtasks = serializers.BooleanField(
        default=True,
        help_text=_('Include subtasks in clone')
    )

    include_comments = serializers.BooleanField(
        default=False,
        help_text=_('Include comments in clone')
    )

    include_attachments = serializers.BooleanField(
        default=False,
        help_text=_('Include attachments in clone')
    )

    include_dependencies = serializers.BooleanField(
        default=True,
        help_text=_('Include dependencies in clone')
    )

    assignee_mapping = serializers.DictField(
        required=False,
        help_text=_('Mapping of old assignee IDs to new assignee IDs')
    )


class ProjectGanttSerializer(serializers.Serializer):
    """Serializer for project Gantt chart data."""

    tasks = serializers.ListField()
    dependencies = serializers.ListField()
    milestones = serializers.ListField()
    resources = serializers.ListField()
    timeline = serializers.DictField()


class SprintBurndownSerializer(serializers.Serializer):
    """Serializer for sprint burndown chart data."""

    dates = serializers.ListField()
    ideal_burndown = serializers.ListField()
    actual_burndown = serializers.ListField()
    scope_changes = serializers.ListField()
    completed_tasks = serializers.ListField()


class ProjectTimelineSerializer(serializers.Serializer):
    """Serializer for project timeline data."""

    phases = serializers.ListField()
    milestones = serializers.ListField()
    dependencies = serializers.ListField()
    critical_path = serializers.ListField()
    resource_allocation = serializers.DictField()


class TaskTimeTrackingSerializer(serializers.Serializer):
    """Serializer for task time tracking data."""

    task_id = serializers.UUIDField()
    logged_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    estimated_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    remaining_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    time_entries = serializers.ListField()
    efficiency = serializers.DecimalField(max_digits=5, decimal_places=2)
    productivity_trend = serializers.ListField()


class ProjectWorkloadSerializer(serializers.Serializer):
    """Serializer for project workload data."""

    team_members = serializers.ListField()
    task_distribution = serializers.DictField()
    capacity_utilization = serializers.DictField()
    workload_trend = serializers.ListField()
    bottlenecks = serializers.ListField()
    recommendations = serializers.ListField()


class ProjectRiskSerializer(serializers.Serializer):
    """Serializer for project risk assessment."""

    risk_level = serializers.CharField()
    risk_factors = serializers.ListField()
    mitigation_strategies = serializers.ListField()
    contingency_plans = serializers.ListField()
    risk_score = serializers.IntegerField()
    risk_trend = serializers.ListField()


class ProjectQualitySerializer(serializers.Serializer):
    """Serializer for project quality metrics."""

    code_quality_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    test_coverage = serializers.DecimalField(max_digits=5, decimal_places=2)
    defect_density = serializers.DecimalField(max_digits=5, decimal_places=2)
    technical_debt = serializers.DecimalField(max_digits=5, decimal_places=2)
    maintainability_index = serializers.DecimalField(max_digits=5, decimal_places=2)
    quality_trend = serializers.ListField()
    recommendations = serializers.ListField()