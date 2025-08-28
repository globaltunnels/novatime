"""
Tests for tasks app.

This module contains comprehensive tests for the tasks app,
including model tests, serializer tests, and view tests.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta

from .models import (
    Project, Task, Assignment, Epic, Sprint, Dependency,
    Template, Comment, Attachment, Tag
)
from .serializers import (
    ProjectSerializer, TaskSerializer, AssignmentSerializer,
    EpicSerializer, SprintSerializer, DependencySerializer,
    TemplateSerializer, CommentSerializer, AttachmentSerializer,
    TagSerializer
)

User = get_user_model()


class ProjectModelTest(TestCase):
    """Test Project model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )

    def test_project_creation(self):
        """Test project creation."""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.slug, 'test-project')
        self.assertEqual(self.project.organization, self.organization)
        self.assertEqual(self.project.workspace, self.workspace)
        self.assertEqual(self.project.created_by, self.user)
        self.assertEqual(self.project.owner, self.user)
        self.assertEqual(self.project.status, 'planning')
        self.assertEqual(self.project.progress_percentage, 0)

    def test_project_str(self):
        """Test project string representation."""
        expected = 'Test Workspace: Test Project'
        self.assertEqual(str(self.project), expected)

    def test_project_task_methods(self):
        """Test project task-related methods."""
        # Initially no tasks
        self.assertEqual(self.project.get_tasks_count(), 0)
        self.assertEqual(self.project.get_completed_tasks_count(), 0)

        # Create a task
        task = Task.objects.create(
            project=self.project,
            title='Test Task',
            created_by=self.user
        )

        # Check counts
        self.assertEqual(self.project.get_tasks_count(), 1)
        self.assertEqual(self.project.get_completed_tasks_count(), 0)

        # Complete the task
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()

        # Update project progress
        self.project._update_progress()
        self.project.save()

        self.assertEqual(self.project.get_completed_tasks_count(), 1)
        self.assertEqual(self.project.progress_percentage, 100)

    def test_project_membership_methods(self):
        """Test project membership methods."""
        # Initially no members
        self.assertEqual(self.project.get_team_members_count(), 0)

        # Add member
        assignment, created = self.project.add_member(self.user, 'member')
        self.assertTrue(created)
        self.assertEqual(assignment.role, 'member')
        self.assertEqual(self.project.get_team_members_count(), 1)

        # Remove member
        result = self.project.remove_member(self.user)
        self.assertTrue(result)
        self.assertEqual(self.project.get_team_members_count(), 0)

    def test_project_access_control(self):
        """Test project access control."""
        # Owner should have access
        self.assertTrue(self.project.can_user_access(self.user))

        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Other user should not have access to private project
        self.project.is_private = True
        self.project.save()
        self.assertFalse(self.project.can_user_access(other_user))

        # Add other user to workspace
        self.workspace.add_member(other_user, 'member')
        self.assertTrue(self.project.can_user_access(other_user))

    def test_project_overdue_status(self):
        """Test project overdue status."""
        # Set end date in the past
        self.project.end_date = timezone.now().date() - timedelta(days=1)
        self.project.status = 'active'
        self.project.save()

        self.assertTrue(self.project.is_overdue())

        # Set end date in the future
        self.project.end_date = timezone.now().date() + timedelta(days=1)
        self.project.save()

        self.assertFalse(self.project.is_overdue())


class TaskModelTest(TestCase):
    """Test Task model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            description='A test task',
            created_by=self.user,
            reporter=self.user
        )

    def test_task_creation(self):
        """Test task creation."""
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.description, 'A test task')
        self.assertEqual(self.task.project, self.project)
        self.assertEqual(self.task.created_by, self.user)
        self.assertEqual(self.task.reporter, self.user)
        self.assertEqual(self.task.status, 'todo')
        self.assertEqual(self.task.priority, 'medium')
        self.assertEqual(self.task.estimated_hours, 0)
        self.assertEqual(self.task.progress_percentage, 0)

    def test_task_str(self):
        """Test task string representation."""
        expected = 'Test Project: Test Task'
        self.assertEqual(str(self.task), expected)

    def test_task_completion(self):
        """Test task completion."""
        # Complete the task
        self.task.status = 'done'
        self.task.completed_at = timezone.now()
        self.task.save()

        self.assertEqual(self.task.status, 'done')
        self.assertIsNotNone(self.task.completed_at)

    def test_task_overdue(self):
        """Test task overdue status."""
        # Set due date in the past
        self.task.due_date = timezone.now().date() - timedelta(days=1)
        self.task.status = 'in_progress'
        self.task.save()

        self.assertTrue(self.task.is_overdue())

        # Set due date in the future
        self.task.due_date = timezone.now().date() + timedelta(days=1)
        self.task.save()

        self.assertFalse(self.task.is_overdue())

    def test_task_subtasks(self):
        """Test task subtasks."""
        # Create a subtask
        subtask = Task.objects.create(
            project=self.project,
            parent_task=self.task,
            title='Subtask',
            created_by=self.user
        )

        # Check relationship
        self.assertIn(subtask, self.task.subtasks.all())
        self.assertEqual(subtask.parent_task, self.task)

    def test_task_dependencies(self):
        """Test task dependencies."""
        # Create another task
        other_task = Task.objects.create(
            project=self.project,
            title='Other Task',
            created_by=self.user
        )

        # Create dependency
        dependency = Dependency.objects.create(
            project=self.project,
            blocking_task=other_task,
            dependent_task=self.task,
            dependency_type='finish_to_start'
        )

        # Check relationships
        self.assertIn(other_task, [d.blocking_task for d in self.task.dependent_dependencies.all()])
        self.assertIn(self.task, [d.dependent_task for d in other_task.blocking_dependencies.all()])

    def test_task_permissions(self):
        """Test task permissions."""
        # Owner should have edit permission
        self.assertTrue(self.task.can_user_edit(self.user))

        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Other user should not have edit permission
        self.assertFalse(self.task.can_user_edit(other_user))

        # Assign task to other user
        self.task.assignee = other_user
        self.task.save()

        # Assignee should have edit permission
        self.assertTrue(self.task.can_user_edit(other_user))


class AssignmentModelTest(TestCase):
    """Test Assignment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.assignment = Assignment.objects.create(
            project=self.project,
            user=self.user,
            role='member',
            load_percentage=100
        )

    def test_assignment_creation(self):
        """Test assignment creation."""
        self.assertEqual(self.assignment.project, self.project)
        self.assertEqual(self.assignment.user, self.user)
        self.assertEqual(self.assignment.role, 'member')
        self.assertEqual(self.assignment.load_percentage, 100)
        self.assertTrue(self.assignment.is_active)

    def test_assignment_str(self):
        """Test assignment string representation."""
        expected = 'Test User - Test Project (member)'
        self.assertEqual(str(self.assignment), expected)


class EpicModelTest(TestCase):
    """Test Epic model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.epic = Epic.objects.create(
            project=self.project,
            name='Test Epic',
            description='A test epic',
            created_by=self.user
        )

    def test_epic_creation(self):
        """Test epic creation."""
        self.assertEqual(self.epic.name, 'Test Epic')
        self.assertEqual(self.epic.description, 'A test epic')
        self.assertEqual(self.epic.project, self.project)
        self.assertEqual(self.epic.created_by, self.user)
        self.assertEqual(self.epic.status, 'planning')
        self.assertEqual(self.epic.priority, 'medium')
        self.assertEqual(self.epic.progress_percentage, 0)

    def test_epic_str(self):
        """Test epic string representation."""
        expected = 'Test Project: Test Epic'
        self.assertEqual(str(self.epic), expected)


class SprintModelTest(TestCase):
    """Test Sprint model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.sprint = Sprint.objects.create(
            project=self.project,
            name='Test Sprint',
            goal='A test sprint goal',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=14),
            created_by=self.user
        )

    def test_sprint_creation(self):
        """Test sprint creation."""
        self.assertEqual(self.sprint.name, 'Test Sprint')
        self.assertEqual(self.sprint.goal, 'A test sprint goal')
        self.assertEqual(self.sprint.project, self.project)
        self.assertEqual(self.sprint.created_by, self.user)
        self.assertEqual(self.sprint.status, 'planning')
        self.assertEqual(self.sprint.planned_capacity, 0)
        self.assertEqual(self.sprint.actual_capacity, 0)

    def test_sprint_str(self):
        """Test sprint string representation."""
        expected = 'Test Project: Test Sprint'
        self.assertEqual(str(self.sprint), expected)

    def test_sprint_status_update(self):
        """Test sprint status update based on dates."""
        # Sprint should be active during its date range
        self.sprint.status = 'active'
        self.sprint.save()
        self.assertEqual(self.sprint.status, 'active')

        # Sprint should be completed after end date
        self.sprint.end_date = timezone.now().date() - timedelta(days=1)
        self.sprint.save()
        self.assertEqual(self.sprint.status, 'completed')


class DependencyModelTest(TestCase):
    """Test Dependency model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.blocking_task = Task.objects.create(
            project=self.project,
            title='Blocking Task',
            created_by=self.user
        )
        self.dependent_task = Task.objects.create(
            project=self.project,
            title='Dependent Task',
            created_by=self.user
        )
        self.dependency = Dependency.objects.create(
            project=self.project,
            blocking_task=self.blocking_task,
            dependent_task=self.dependent_task,
            dependency_type='finish_to_start',
            lag_days=0
        )

    def test_dependency_creation(self):
        """Test dependency creation."""
        self.assertEqual(self.dependency.project, self.project)
        self.assertEqual(self.dependency.blocking_task, self.blocking_task)
        self.assertEqual(self.dependency.dependent_task, self.dependent_task)
        self.assertEqual(self.dependency.dependency_type, 'finish_to_start')
        self.assertEqual(self.dependency.lag_days, 0)

    def test_dependency_str(self):
        """Test dependency string representation."""
        expected = 'Blocking Task → Dependent Task'
        self.assertEqual(str(self.dependency), expected)


class TemplateModelTest(TestCase):
    """Test Template model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.template = Template.objects.create(
            name='Test Template',
            description='A test template',
            template_type='project',
            template_data={'key': 'value'},
            organization=self.organization,
            created_by=self.user
        )

    def test_template_creation(self):
        """Test template creation."""
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.description, 'A test template')
        self.assertEqual(self.template.template_type, 'project')
        self.assertEqual(self.template.template_data, {'key': 'value'})
        self.assertEqual(self.template.organization, self.organization)
        self.assertEqual(self.template.created_by, self.user)
        self.assertFalse(self.template.is_public)
        self.assertFalse(self.template.is_system)
        self.assertEqual(self.template.usage_count, 0)

    def test_template_str(self):
        """Test template string representation."""
        expected = 'project: Test Template'
        self.assertEqual(str(self.template), expected)

    def test_template_usage_increment(self):
        """Test template usage increment."""
        self.template.increment_usage()
        self.assertEqual(self.template.usage_count, 1)


class CommentModelTest(TestCase):
    """Test Comment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            created_by=self.user,
            owner=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            created_by=self.user
        )
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='This is a test comment'
        )

    def test_comment_creation(self):
        """Test comment creation."""
        self.assertEqual(self.comment.task, self.task)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'This is a test comment')
        self.assertIsNone(self.comment.parent_comment)

    def test_comment_str(self):
        """Test comment string representation."""
        expected = 'Test User: This is a test comment...'
        self.assertEqual(str(self.comment), expected)

    def test_comment_replies(self):
        """Test comment replies."""
        reply = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='This is a reply',
            parent_comment=self.comment
        )

        self.assertIn(reply, self.comment.replies.all())
        self.assertEqual(reply.parent_comment, self.comment)


class TagModelTest(TestCase):
    """Test Tag model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user,
            owner=self.user
        )
        self.tag = Tag.objects.create(
            name='test-tag',
            description='A test tag',
            color='#2563EB',
            organization=self.organization,
            created_by=self.user
        )

    def test_tag_creation(self):
        """Test tag creation."""
        self.assertEqual(self.tag.name, 'test-tag')
        self.assertEqual(self.tag.description, 'A test tag')
        self.assertEqual(self.tag.color, '#2563EB')
        self.assertEqual(self.tag.organization, self.organization)
        self.assertEqual(self.tag.created_by, self.user)
        self.assertEqual(self.tag.usage_count, 0)

    def test_tag_str(self):
        """Test tag string representation."""
        self.assertEqual(str(self.tag), 'test-tag')

    def test_tag_usage_increment(self):
        """Test tag usage increment."""
        self.tag.increment_usage()
        self.assertEqual(self.tag.usage_count, 1)


# Pytest-style tests
@pytest.mark.django_db
def test_project_serializer():
    """Test ProjectSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )

    serializer = ProjectSerializer(project)
    data = serializer.data

    assert data['name'] == 'Test Project'
    assert data['slug'] == 'test-project'
    assert data['tasks_count'] == 0
    assert data['completed_tasks_count'] == 0
    assert data['team_members_count'] == 0
    assert data['is_overdue'] is False


@pytest.mark.django_db
def test_task_serializer():
    """Test TaskSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        created_by=user,
        reporter=user
    )

    serializer = TaskSerializer(task)
    data = serializer.data

    assert data['title'] == 'Test Task'
    assert data['status'] == 'todo'
    assert data['priority'] == 'medium'
    assert data['logged_hours'] == 0
    assert data['remaining_hours'] == 0
    assert data['is_overdue'] is False


@pytest.mark.django_db
def test_assignment_serializer():
    """Test AssignmentSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    assignment = Assignment.objects.create(
        project=project,
        user=user,
        role='member',
        load_percentage=100
    )

    serializer = AssignmentSerializer(assignment)
    data = serializer.data

    assert data['role'] == 'member'
    assert data['load_percentage'] == 100
    assert data['is_active'] is True


@pytest.mark.django_db
def test_epic_serializer():
    """Test EpicSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    epic = Epic.objects.create(
        project=project,
        name='Test Epic',
        created_by=user
    )

    serializer = EpicSerializer(epic)
    data = serializer.data

    assert data['name'] == 'Test Epic'
    assert data['status'] == 'planning'
    assert data['priority'] == 'medium'
    assert data['progress_percentage'] == 0


@pytest.mark.django_db
def test_sprint_serializer():
    """Test SprintSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    sprint = Sprint.objects.create(
        project=project,
        name='Test Sprint',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=14),
        created_by=user
    )

    serializer = SprintSerializer(sprint)
    data = serializer.data

    assert data['name'] == 'Test Sprint'
    assert data['status'] == 'planning'
    assert data['planned_capacity'] == 0
    assert data['actual_capacity'] == 0


@pytest.mark.django_db
def test_dependency_serializer():
    """Test DependencySerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    blocking_task = Task.objects.create(
        project=project,
        title='Blocking Task',
        created_by=user
    )
    dependent_task = Task.objects.create(
        project=project,
        title='Dependent Task',
        created_by=user
    )
    dependency = Dependency.objects.create(
        project=project,
        blocking_task=blocking_task,
        dependent_task=dependent_task,
        dependency_type='finish_to_start'
    )

    serializer = DependencySerializer(dependency)
    data = serializer.data

    assert data['dependency_type'] == 'finish_to_start'
    assert data['lag_days'] == 0
    assert data['blocking_task_title'] == 'Blocking Task'
    assert data['dependent_task_title'] == 'Dependent Task'


@pytest.mark.django_db
def test_template_serializer():
    """Test TemplateSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    template = Template.objects.create(
        name='Test Template',
        template_type='project',
        template_data={'key': 'value'},
        organization=organization,
        created_by=user
    )

    serializer = TemplateSerializer(template)
    data = serializer.data

    assert data['name'] == 'Test Template'
    assert data['template_type'] == 'project'
    assert data['template_data'] == {'key': 'value'}
    assert data['usage_count'] == 0


@pytest.mark.django_db
def test_comment_serializer():
    """Test CommentSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        created_by=user
    )
    comment = Comment.objects.create(
        task=task,
        author=user,
        content='This is a test comment'
    )

    serializer = CommentSerializer(comment)
    data = serializer.data

    assert data['content'] == 'This is a test comment'
    assert data['replies_count'] == 0
    assert data['replies'] == []


@pytest.mark.django_db
def test_tag_serializer():
    """Test TagSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    tag = Tag.objects.create(
        name='test-tag',
        organization=organization,
        created_by=user
    )

    serializer = TagSerializer(tag)
    data = serializer.data

    assert data['name'] == 'test-tag'
    assert data['usage_count'] == 0


@pytest.mark.django_db
def test_project_workflow():
    """Test complete project workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )

    # Create project
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )

    assert project.name == 'Test Project'
    assert project.status == 'planning'
    assert project.progress_percentage == 0

    # Add team member
    assignment, created = project.add_member(user, 'member')
    assert created is True
    assert project.get_team_members_count() == 1

    # Create tasks
    task1 = Task.objects.create(
        project=project,
        title='Task 1',
        created_by=user,
        reporter=user
    )
    task2 = Task.objects.create(
        project=project,
        title='Task 2',
        created_by=user,
        reporter=user
    )

    assert project.get_tasks_count() == 2

    # Complete a task
    task1.status = 'done'
    task1.completed_at = timezone.now()
    task1.save()

    # Update project progress
    project._update_progress()
    project.save()

    assert project.get_completed_tasks_count() == 1
    assert project.progress_percentage == 50


@pytest.mark.django_db
def test_task_workflow():
    """Test complete task workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )

    # Create task
    task = Task.objects.create(
        project=project,
        title='Test Task',
        description='A test task',
        priority='high',
        estimated_hours=8,
        created_by=user,
        reporter=user
    )

    assert task.status == 'todo'
    assert task.priority == 'high'
    assert task.estimated_hours == 8

    # Assign task
    task.assignee = user
    task.save()

    assert task.assignee == user

    # Start task
    task.status = 'in_progress'
    task.save()

    assert task.status == 'in_progress'

    # Complete task
    task.status = 'done'
    task.completed_at = timezone.now()
    task.save()

    assert task.status == 'done'
    assert task.completed_at is not None


@pytest.mark.django_db
def test_sprint_workflow():
    """Test complete sprint workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )

    # Create sprint
    sprint = Sprint.objects.create(
        project=project,
        name='Test Sprint',
        goal='Complete all tasks',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=14),
        planned_capacity=80,
        created_by=user
    )

    assert sprint.status == 'planning'
    assert sprint.planned_capacity == 80

    # Activate sprint
    sprint.status = 'active'
    sprint.save()

    assert sprint.status == 'active'

    # Create task in sprint
    task = Task.objects.create(
        project=project,
        title='Sprint Task',
        sprint=sprint,
        created_by=user,
        reporter=user
    )

    assert task.sprint == sprint
    assert sprint.tasks.count() == 1


@pytest.mark.django_db
def test_dependency_workflow():
    """Test complete dependency workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )

    # Create tasks
    task1 = Task.objects.create(
        project=project,
        title='Task 1',
        created_by=user
    )
    task2 = Task.objects.create(
        project=project,
        title='Task 2',
        created_by=user
    )

    # Create dependency
    dependency = Dependency.objects.create(
        project=project,
        blocking_task=task1,
        dependent_task=task2,
        dependency_type='finish_to_start'
    )

    assert dependency.blocking_task == task1
    assert dependency.dependent_task == task2

    # Check task relationships
    assert task1 in [d.blocking_task for d in task2.dependent_dependencies.all()]
    assert task2 in [d.dependent_task for d in task1.blocking_dependencies.all()]


@pytest.mark.django_db
def test_template_workflow():
    """Test complete template workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    # Create template
    template_data = {
        'name': 'Test Project',
        'description': 'A test project',
        'project_type': 'software',
        'methodology': 'agile',
        'tasks': [
            {
                'title': 'Setup project',
                'description': 'Initial project setup',
                'priority': 'high',
                'estimated_hours': 4
            }
        ]
    }

    template = Template.objects.create(
        name='Test Template',
        description='A test template',
        template_type='project',
        template_data=template_data,
        organization=organization,
        created_by=user
    )

    assert template.template_type == 'project'
    assert template.usage_count == 0

    # Increment usage
    template.increment_usage()
    assert template.usage_count == 1


@pytest.mark.django_db
def test_comment_workflow():
    """Test complete comment workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        organization=organization,
        workspace=workspace,
        name='Test Project',
        slug='test-project',
        created_by=user,
        owner=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        created_by=user
    )

    # Create comment
    comment = Comment.objects.create(
        task=task,
        author=user,
        content='This is a test comment'
    )

    assert comment.content == 'This is a test comment'
    assert comment.task == task
    assert comment.author == user

    # Create reply
    reply = Comment.objects.create(
        task=task,
        author=user,
        content='This is a reply',
        parent_comment=comment
    )

    assert reply.parent_comment == comment
    assert reply in comment.replies.all()


@pytest.mark.django_db
def test_tag_workflow():
    """Test complete tag workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user,
        owner=user
    )

    # Create tag
    tag = Tag.objects.create(
        name='urgent',
        description='Urgent tasks',
        color='#EF4444',
        organization=organization,
        created_by=user
    )

    assert tag.name == 'urgent'
    assert tag.usage_count == 0

    # Increment usage
    tag.increment_usage()
    assert tag.usage_count == 1