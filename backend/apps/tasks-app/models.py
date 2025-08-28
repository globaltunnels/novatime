"""
Tasks models for NovaTime.

This app handles project management, task tracking, assignments,
dependencies, templates, and AI-assisted planning features.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Project(models.Model):
    """
    Project model for organizing work within workspaces.

    Represents a project that contains tasks, epics, and sprints.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Project name')
    )

    slug = models.SlugField(
        _('slug'),
        max_length=100,
        help_text=_('URL-friendly identifier')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Project description')
    )

    # Project details
    project_type = models.CharField(
        _('project type'),
        max_length=20,
        choices=[
            ('software', 'Software Development'),
            ('marketing', 'Marketing'),
            ('design', 'Design'),
            ('research', 'Research'),
            ('operations', 'Operations'),
            ('sales', 'Sales'),
            ('hr', 'Human Resources'),
            ('finance', 'Finance'),
            ('other', 'Other'),
        ],
        default='software',
        help_text=_('Type of project')
    )

    methodology = models.CharField(
        _('methodology'),
        max_length=20,
        choices=[
            ('agile', 'Agile'),
            ('waterfall', 'Waterfall'),
            ('kanban', 'Kanban'),
            ('scrum', 'Scrum'),
            ('hybrid', 'Hybrid'),
            ('custom', 'Custom'),
        ],
        default='agile',
        help_text=_('Project management methodology')
    )

    # Status and progress
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('active', 'Active'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='planning',
        help_text=_('Current project status')
    )

    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=[
            ('lowest', 'Lowest'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('highest', 'Highest'),
        ],
        default='medium',
        help_text=_('Project priority')
    )

    progress_percentage = models.PositiveIntegerField(
        _('progress percentage'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Project completion percentage')
    )

    # Dates
    start_date = models.DateField(
        _('start date'),
        null=True,
        blank=True,
        help_text=_('Project start date')
    )

    end_date = models.DateField(
        _('end date'),
        null=True,
        blank=True,
        help_text=_('Project end date')
    )

    actual_end_date = models.DateField(
        _('actual end date'),
        null=True,
        blank=True,
        help_text=_('Actual project completion date')
    )

    # Budget and estimates
    budget = models.DecimalField(
        _('budget'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Project budget')
    )

    estimated_hours = models.DecimalField(
        _('estimated hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Total estimated hours for the project')
    )

    actual_hours = models.DecimalField(
        _('actual hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Total actual hours logged on the project')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='projects',
        help_text=_('Organization this project belongs to')
    )

    workspace = models.ForeignKey(
        'organizations.Workspace',
        on_delete=models.CASCADE,
        related_name='projects',
        help_text=_('Workspace this project belongs to')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        help_text=_('User who created this project')
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_projects',
        help_text=_('Current project owner')
    )

    # Settings
    is_private = models.BooleanField(
        _('private'),
        default=False,
        help_text=_('Whether this project is private')
    )

    allow_guest_access = models.BooleanField(
        _('allow guest access'),
        default=False,
        help_text=_('Whether guests can access this project')
    )

    require_time_tracking = models.BooleanField(
        _('require time tracking'),
        default=False,
        help_text=_('Whether time tracking is required for all tasks')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        unique_together = ['workspace', 'slug']
        indexes = [
            models.Index(fields=['organization', 'workspace']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.workspace.name}: {self.name}"

    def save(self, *args, **kwargs):
        """Save project and handle related updates."""
        # Set owner as creator if not set
        if not self.owner and self.created_by:
            self.owner = self.created_by

        # Auto-calculate progress if not set
        if self.pk:
            self._update_progress()

        super().save(*args, **kwargs)

    def _update_progress(self):
        """Update project progress based on tasks."""
        total_tasks = self.tasks.count()
        if total_tasks > 0:
            completed_tasks = self.tasks.filter(status='done').count()
            self.progress_percentage = int((completed_tasks / total_tasks) * 100)

    def get_tasks_count(self):
        """Get total number of tasks."""
        return self.tasks.count()

    def get_completed_tasks_count(self):
        """Get number of completed tasks."""
        return self.tasks.filter(status='done').count()

    def get_overdue_tasks_count(self):
        """Get number of overdue tasks."""
        return self.tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress']
        ).count()

    def get_team_members_count(self):
        """Get number of team members."""
        return self.assignments.values('user').distinct().count()

    def get_total_estimated_hours(self):
        """Get total estimated hours for all tasks."""
        return self.tasks.aggregate(
            total=models.Sum('estimated_hours')
        )['total'] or 0

    def get_total_logged_hours(self):
        """Get total logged hours for all tasks."""
        return self.tasks.aggregate(
            total=models.Sum('time_entries__duration_minutes')
        )['total'] or 0

    def get_budget_utilization(self):
        """Get budget utilization percentage."""
        if not self.budget or self.budget == 0:
            return 0

        # This would need integration with billing
        return 0  # Placeholder

    def is_overdue(self):
        """Check if project is overdue."""
        if self.end_date and self.status in ['planning', 'active']:
            return timezone.now().date() > self.end_date
        return False

    def is_on_track(self):
        """Check if project is on track."""
        if not self.end_date:
            return True

        total_days = (self.end_date - self.start_date).days if self.start_date else 0
        elapsed_days = (timezone.now().date() - self.start_date).days if self.start_date else 0

        if total_days == 0:
            return True

        expected_progress = (elapsed_days / total_days) * 100
        return self.progress_percentage >= expected_progress * 0.8  # 80% threshold

    def add_member(self, user, role='member'):
        """Add a user to the project."""
        assignment, created = Assignment.objects.get_or_create(
            project=self,
            user=user,
            defaults={'role': role}
        )
        return assignment, created

    def remove_member(self, user):
        """Remove a user from the project."""
        return Assignment.objects.filter(
            project=self,
            user=user
        ).delete()[0] > 0

    def can_user_access(self, user):
        """Check if user can access this project."""
        if self.is_private:
            return self.assignments.filter(user=user).exists()
        else:
            # Check workspace membership
            return self.workspace.memberships.filter(
                user=user,
                is_active=True
            ).exists()


class Task(models.Model):
    """
    Task model for individual work items within projects.

    Represents a single task that can be assigned, tracked, and completed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    title = models.CharField(
        _('title'),
        max_length=500,
        help_text=_('Task title')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Task description')
    )

    # Status and priority
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('done', 'Done'),
            ('blocked', 'Blocked'),
        ],
        default='todo',
        help_text=_('Current task status')
    )

    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=[
            ('lowest', 'Lowest'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('highest', 'Highest'),
        ],
        default='medium',
        help_text=_('Task priority')
    )

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text=_('Project this task belongs to')
    )

    epic = models.ForeignKey(
        'Epic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text=_('Epic this task belongs to')
    )

    sprint = models.ForeignKey(
        'Sprint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text=_('Sprint this task belongs to')
    )

    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subtasks',
        help_text=_('Parent task (for subtasks)')
    )

    # Assignment
    assignee = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text=_('User assigned to this task')
    )

    reporter = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_tasks',
        help_text=_('User who reported this task')
    )

    # Dates
    due_date = models.DateField(
        _('due date'),
        null=True,
        blank=True,
        help_text=_('Task due date')
    )

    completed_at = models.DateTimeField(
        _('completed at'),
        null=True,
        blank=True,
        help_text=_('When the task was completed')
    )

    # Estimates and tracking
    estimated_hours = models.DecimalField(
        _('estimated hours'),
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('Estimated hours to complete the task')
    )

    actual_hours = models.DecimalField(
        _('actual hours'),
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('Actual hours logged on the task')
    )

    # Progress
    progress_percentage = models.PositiveIntegerField(
        _('progress percentage'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Task completion percentage')
    )

    # Labels and categorization
    labels = models.JSONField(
        _('labels'),
        default=list,
        blank=True,
        help_text=_('Task labels/tags')
    )

    # Custom fields
    custom_fields = models.JSONField(
        _('custom fields'),
        default=dict,
        blank=True,
        help_text=_('Custom fields for additional task data')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        help_text=_('User who created this task')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['project', 'assignee']),
            models.Index(fields=['assignee', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.project.name}: {self.title}"

    def save(self, *args, **kwargs):
        """Save task and handle related updates."""
        # Auto-set reporter as creator if not set
        if not self.reporter and self.created_by:
            self.reporter = self.created_by

        # Auto-set completed_at when status changes to done
        if self.status == 'done' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'done':
            self.completed_at = None

        # Update project progress
        if self.pk:
            self.project._update_progress()
            self.project.save()

        super().save(*args, **kwargs)

    def get_logged_hours(self):
        """Get total logged hours for this task."""
        return self.time_entries.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0

    def get_remaining_hours(self):
        """Get remaining hours to complete the task."""
        logged_hours = self.get_logged_hours() / 60
        return max(0, float(self.estimated_hours) - logged_hours)

    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status in ['todo', 'in_progress', 'review']:
            return timezone.now().date() > self.due_date
        return False

    def get_blocking_tasks(self):
        """Get tasks that are blocking this task."""
        return Task.objects.filter(
            project=self.project,
            dependencies__dependent_task=self
        )

    def get_blocked_tasks(self):
        """Get tasks that this task is blocking."""
        return Task.objects.filter(
            project=self.project,
            dependencies__blocking_task=self
        )

    def can_user_edit(self, user):
        """Check if user can edit this task."""
        # Owner can edit
        if self.project.owner == user:
            return True

        # Assignee can edit
        if self.assignee == user:
            return True

        # Project members can edit
        return self.project.assignments.filter(user=user).exists()

    def update_progress(self):
        """Update task progress based on subtasks."""
        if self.subtasks.exists():
            total_subtasks = self.subtasks.count()
            completed_subtasks = self.subtasks.filter(status='done').count()
            self.progress_percentage = int((completed_subtasks / total_subtasks) * 100)
        else:
            # Manual progress or based on status
            if self.status == 'done':
                self.progress_percentage = 100
            elif self.status == 'in_progress':
                self.progress_percentage = max(self.progress_percentage, 25)
            elif self.status == 'review':
                self.progress_percentage = max(self.progress_percentage, 75)


class Assignment(models.Model):
    """
    Assignment model for user-task relationships.

    Represents a user's assignment to a project or task with specific roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text=_('Project this assignment belongs to')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='project_assignments',
        help_text=_('User who is assigned')
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assignments',
        help_text=_('Specific task assignment (optional)')
    )

    # Assignment details
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('lead', 'Lead'),
            ('developer', 'Developer'),
            ('designer', 'Designer'),
            ('qa', 'QA'),
            ('reviewer', 'Reviewer'),
            ('member', 'Member'),
        ],
        default='member',
        help_text=_('Role in the project/task')
    )

    load_percentage = models.PositiveIntegerField(
        _('load percentage'),
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text=_('Percentage of time allocated to this assignment')
    )

    # Dates
    start_date = models.DateField(
        _('start date'),
        null=True,
        blank=True,
        help_text=_('Assignment start date')
    )

    end_date = models.DateField(
        _('end date'),
        null=True,
        blank=True,
        help_text=_('Assignment end date')
    )

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this assignment is active')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'user']
        verbose_name = _('assignment')
        verbose_name_plural = _('assignments')
        unique_together = ['project', 'user', 'task']
        indexes = [
            models.Index(fields=['project', 'user']),
            models.Index(fields=['project', 'role']),
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['task', 'user']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        task_str = f" - {self.task.title}" if self.task else ""
        return f"{self.user.get_full_name()} - {self.project.name}{task_str} ({self.role})"


class Epic(models.Model):
    """
    Epic model for grouping related tasks.

    Represents a large body of work that can be broken down into smaller tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Epic name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Epic description')
    )

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='epics',
        help_text=_('Project this epic belongs to')
    )

    # Status and priority
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='planning',
        help_text=_('Current epic status')
    )

    priority = models.CharField(
        _('priority'),
        max_length=10,
        choices=[
            ('lowest', 'Lowest'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('highest', 'Highest'),
        ],
        default='medium',
        help_text=_('Epic priority')
    )

    # Progress
    progress_percentage = models.PositiveIntegerField(
        _('progress percentage'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Epic completion percentage')
    )

    # Estimates
    estimated_hours = models.DecimalField(
        _('estimated hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Total estimated hours for the epic')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_epics',
        help_text=_('User who created this epic')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'name']
        verbose_name = _('epic')
        verbose_name_plural = _('epics')
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.project.name}: {self.name}"

    def save(self, *args, **kwargs):
        """Save epic and update progress."""
        if self.pk:
            self._update_progress()
        super().save(*args, **kwargs)

    def _update_progress(self):
        """Update epic progress based on tasks."""
        total_tasks = self.tasks.count()
        if total_tasks > 0:
            completed_tasks = self.tasks.filter(status='done').count()
            self.progress_percentage = int((completed_tasks / total_tasks) * 100)


class Sprint(models.Model):
    """
    Sprint model for time-boxed development iterations.

    Represents a sprint that contains tasks to be completed within a time frame.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Sprint name')
    )

    goal = models.TextField(
        _('goal'),
        blank=True,
        help_text=_('Sprint goal')
    )

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sprints',
        help_text=_('Project this sprint belongs to')
    )

    # Dates
    start_date = models.DateField(
        _('start date'),
        help_text=_('Sprint start date')
    )

    end_date = models.DateField(
        _('end date'),
        help_text=_('Sprint end date')
    )

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='planning',
        help_text=_('Current sprint status')
    )

    # Capacity and estimates
    planned_capacity = models.DecimalField(
        _('planned capacity'),
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('Planned sprint capacity in hours')
    )

    actual_capacity = models.DecimalField(
        _('actual capacity'),
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('Actual sprint capacity used')
    )

    # Relationships
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sprints',
        help_text=_('User who created this sprint')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', '-start_date']
        verbose_name = _('sprint')
        verbose_name_plural = _('sprints')
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'start_date']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.project.name}: {self.name}"

    def save(self, *args, **kwargs):
        """Save sprint and handle related updates."""
        # Auto-set status based on dates
        today = timezone.now().date()
        if self.start_date <= today <= self.end_date:
            if self.status == 'planning':
                self.status = 'active'
        elif today > self.end_date:
            if self.status == 'active':
                self.status = 'completed'

        super().save(*args, **kwargs)

    def get_tasks_count(self):
        """Get total number of tasks in sprint."""
        return self.tasks.count()

    def get_completed_tasks_count(self):
        """Get number of completed tasks."""
        return self.tasks.filter(status='done').count()

    def get_remaining_capacity(self):
        """Get remaining capacity."""
        return max(0, float(self.planned_capacity) - float(self.actual_capacity))

    def is_overdue(self):
        """Check if sprint is overdue."""
        if self.status in ['planning', 'active']:
            return timezone.now().date() > self.end_date
        return False


class Dependency(models.Model):
    """
    Dependency model for task relationships.

    Represents dependencies between tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='dependencies',
        help_text=_('Project this dependency belongs to')
    )

    blocking_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='blocking_dependencies',
        help_text=_('Task that must be completed first')
    )

    dependent_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependent_dependencies',
        help_text=_('Task that depends on the blocking task')
    )

    # Dependency type
    dependency_type = models.CharField(
        _('dependency type'),
        max_length=20,
        choices=[
            ('finish_to_start', 'Finish to Start'),
            ('start_to_start', 'Start to Start'),
            ('finish_to_finish', 'Finish to Finish'),
            ('start_to_finish', 'Start to Finish'),
        ],
        default='finish_to_start',
        help_text=_('Type of dependency relationship')
    )

    # Lag time
    lag_days = models.IntegerField(
        _('lag days'),
        default=0,
        help_text=_('Lag time in days between tasks')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'blocking_task', 'dependent_task']
        verbose_name = _('dependency')
        verbose_name_plural = _('dependencies')
        unique_together = ['blocking_task', 'dependent_task']
        indexes = [
            models.Index(fields=['project', 'blocking_task']),
            models.Index(fields=['project', 'dependent_task']),
            models.Index(fields=['blocking_task']),
            models.Index(fields=['dependent_task']),
            models.Index(fields=['dependency_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.blocking_task.title} → {self.dependent_task.title}"


class Template(models.Model):
    """
    Template model for reusable project and task templates.

    Represents templates that can be used to create new projects or tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('Template name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Template description')
    )

    # Template type
    template_type = models.CharField(
        _('template type'),
        max_length=20,
        choices=[
            ('project', 'Project Template'),
            ('task', 'Task Template'),
            ('epic', 'Epic Template'),
        ],
        help_text=_('Type of template')
    )

    # Template data
    template_data = models.JSONField(
        _('template data'),
        help_text=_('JSON data containing template configuration')
    )

    # Visibility
    is_public = models.BooleanField(
        _('public'),
        default=False,
        help_text=_('Whether this template is publicly available')
    )

    is_system = models.BooleanField(
        _('system template'),
        default=False,
        help_text=_('Whether this is a system-provided template')
    )

    # Usage statistics
    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this template has been used')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='templates',
        help_text=_('Organization this template belongs to (null for system templates)')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates',
        help_text=_('User who created this template')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        verbose_name = _('template')
        verbose_name_plural = _('templates')
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['organization', 'template_type']),
            models.Index(fields=['is_public']),
            models.Index(fields=['is_system']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.template_type.title()}: {self.name}"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class Comment(models.Model):
    """
    Comment model for task discussions.

    Represents comments and discussions on tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text=_('Task this comment belongs to')
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='task_comments',
        help_text=_('User who wrote this comment')
    )

    # Comment content
    content = models.TextField(
        _('content'),
        help_text=_('Comment content')
    )

    # Threading
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text=_('Parent comment (for threaded replies)')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent_comment']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.author.get_full_name()}: {self.content[:50]}..."

    def get_replies(self):
        """Get all replies to this comment."""
        return Comment.objects.filter(parent_comment=self)


class Attachment(models.Model):
    """
    Attachment model for task file attachments.

    Represents files attached to tasks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_('Task this attachment belongs to')
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='uploaded_attachments',
        help_text=_('User who uploaded this attachment')
    )

    # File information
    file = models.FileField(
        _('file'),
        upload_to='tasks/attachments/',
        help_text=_('Uploaded file')
    )

    filename = models.CharField(
        _('filename'),
        max_length=255,
        help_text=_('Original filename')
    )

    file_size = models.PositiveIntegerField(
        _('file size'),
        help_text=_('File size in bytes')
    )

    content_type = models.CharField(
        _('content type'),
        max_length=100,
        help_text=_('File content type')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['content_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.task.title}: {self.filename}"


class Tag(models.Model):
    """
    Tag model for task categorization.

    Represents tags that can be applied to tasks for organization.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic information
    name = models.CharField(
        _('name'),
        max_length=50,
        unique=True,
        help_text=_('Tag name')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Tag description')
    )

    # Appearance
    color = models.CharField(
        _('color'),
        max_length=7,
        default='#2563EB',
        help_text=_('Tag color (hex code)')
    )

    # Usage
    usage_count = models.PositiveIntegerField(
        _('usage count'),
        default=0,
        help_text=_('Number of times this tag has been used')
    )

    # Relationships
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='tags',
        help_text=_('Organization this tag belongs to')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tags',
        help_text=_('User who created this tag')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'usage_count']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    def decrement_usage(self):
        """Decrement usage count."""
        if self.usage_count > 0:
            self.usage_count -= 1
            self.save(update_fields=['usage_count'])


# Add reverse relationships
Project.add_to_class(
    'time_entries',
    models.ManyToManyField(
        'time_entries.TimeEntry',
        through='time_entries.TimeEntry',
        related_name='projects',
        help_text=_('Time entries for this project')
    )
)

Task.add_to_class(
    'time_entries',
    models.ManyToManyField(
        'time_entries.TimeEntry',
        through='time_entries.TimeEntry',
        related_name='tasks',
        help_text=_('Time entries for this task')
    )
)