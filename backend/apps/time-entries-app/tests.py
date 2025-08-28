"""
Tests for time entries app.

This module contains comprehensive tests for the time entries app,
including model tests, serializer tests, and view tests.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta

from organizations.models import Organization, Workspace
from tasks.models import Project, Task
from .models import (
    TimeEntry, Timer, IdlePeriod, TimeEntryTemplate, TimeEntryComment
)
from .serializers import (
    TimeEntrySerializer, TimerSerializer, IdlePeriodSerializer,
    TimeEntryTemplateSerializer, TimeEntryCommentSerializer
)

User = get_user_model()


class TimeEntryModelTest(TestCase):
    """Test TimeEntry model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            key='TEST',
            created_by=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            reporter=self.user
        )

    def test_time_entry_creation(self):
        """Test time entry creation."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)

        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time,
            description='Test time entry'
        )

        self.assertEqual(time_entry.user, self.user)
        self.assertEqual(time_entry.workspace, self.workspace)
        self.assertEqual(time_entry.task, self.task)
        self.assertEqual(time_entry.duration_minutes, 120)
        self.assertEqual(time_entry.description, 'Test time entry')
        self.assertTrue(time_entry.is_running())

    def test_time_entry_str(self):
        """Test time entry string representation."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1, minutes=30)

        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time
        )

        expected = f"{self.user.get_full_name()}: 90min - Test Task"
        self.assertEqual(str(time_entry), expected)

    def test_get_duration_display(self):
        """Test duration display formatting."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2, minutes=30)

        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time
        )

        self.assertEqual(time_entry.get_duration_display(), "2h 30m")

        # Test short duration
        time_entry.duration_minutes = 45
        self.assertEqual(time_entry.get_duration_display(), "45m")

    def test_get_cost_display(self):
        """Test cost display formatting."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)

        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time,
            hourly_rate=50.00
        )

        self.assertEqual(time_entry.get_cost_display(), "$50.00")

        # Test zero cost
        time_entry.cost_amount = 0
        self.assertEqual(time_entry.get_cost_display(), "$0.00")

    def test_approve_reject(self):
        """Test approval workflow."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)

        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time
        )

        # Initially not approved
        self.assertIsNone(time_entry.is_approved)

        # Approve
        time_entry.approve(self.user, 'Good work!')
        self.assertTrue(time_entry.is_approved)
        self.assertEqual(time_entry.approved_by, self.user)
        self.assertEqual(time_entry.approval_notes, 'Good work!')

        # Reject
        time_entry.reject(self.user, 'Needs improvement')
        self.assertFalse(time_entry.is_approved)
        self.assertEqual(time_entry.approval_notes, 'Needs improvement')

    def test_get_overlap_entries(self):
        """Test overlapping time entries detection."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)

        # Create first time entry
        time_entry1 = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time
        )

        # Create overlapping time entry
        overlap_start = start_time + timedelta(hours=1)
        overlap_end = end_time + timedelta(hours=1)

        time_entry2 = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=overlap_start,
            end_time=overlap_end
        )

        overlaps = time_entry1.get_overlap_entries()
        self.assertEqual(len(overlaps), 1)
        self.assertEqual(overlaps[0], time_entry2)


class TimerModelTest(TestCase):
    """Test Timer model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            key='TEST',
            created_by=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            reporter=self.user
        )

    def test_timer_creation(self):
        """Test timer creation."""
        start_time = timezone.now()

        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            description='Test timer'
        )

        self.assertEqual(timer.user, self.user)
        self.assertEqual(timer.workspace, self.workspace)
        self.assertEqual(timer.task, self.task)
        self.assertEqual(timer.status, 'running')
        self.assertEqual(timer.description, 'Test timer')

    def test_timer_str(self):
        """Test timer string representation."""
        start_time = timezone.now()

        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time
        )

        duration = timer.get_current_duration_display()
        expected = f"{self.user.get_full_name()}: {duration} - Test Task (running)"
        self.assertEqual(str(timer), expected)

    def test_pause_resume(self):
        """Test timer pause and resume."""
        start_time = timezone.now()

        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time
        )

        # Initially running
        self.assertEqual(timer.status, 'running')

        # Pause
        timer.pause()
        self.assertEqual(timer.status, 'paused')
        self.assertIsNotNone(timer.paused_at)

        # Resume
        timer.resume()
        self.assertEqual(timer.status, 'running')
        self.assertIsNone(timer.paused_at)

    def test_stop_and_create_time_entry(self):
        """Test stopping timer and creating time entry."""
        start_time = timezone.now()

        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            description='Test timer'
        )

        # Stop after some time
        end_time = start_time + timedelta(hours=1, minutes=30)
        time_entry = timer.stop(end_time)

        # Check timer
        self.assertEqual(timer.status, 'stopped')

        # Check time entry
        self.assertIsNotNone(time_entry)
        self.assertEqual(time_entry.user, self.user)
        self.assertEqual(time_entry.task, self.task)
        self.assertEqual(time_entry.duration_minutes, 90)
        self.assertEqual(time_entry.description, 'Test timer')

    def test_get_current_duration(self):
        """Test current duration calculation."""
        start_time = timezone.now()

        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time
        )

        # Simulate 1 hour and 30 minutes passed
        timer.start_time = start_time - timedelta(hours=1, minutes=30)
        timer.save()

        duration_minutes = timer.get_current_duration_minutes()
        self.assertEqual(duration_minutes, 90)


class IdlePeriodModelTest(TestCase):
    """Test IdlePeriod model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            key='TEST',
            created_by=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            reporter=self.user
        )
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2)
        )

    def test_idle_period_creation(self):
        """Test idle period creation."""
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=15)

        idle_period = IdlePeriod.objects.create(
            time_entry=self.time_entry,
            start_time=start_time,
            end_time=end_time,
            detection_method='system'
        )

        self.assertEqual(idle_period.time_entry, self.time_entry)
        self.assertEqual(idle_period.duration_minutes, 15)
        self.assertEqual(idle_period.detection_method, 'system')

    def test_idle_period_str(self):
        """Test idle period string representation."""
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=10)

        idle_period = IdlePeriod.objects.create(
            time_entry=self.time_entry,
            start_time=start_time,
            end_time=end_time,
            detection_method='system'
        )

        expected = f"Idle: 10min during {self.time_entry}"
        self.assertEqual(str(idle_period), expected)


class TimeEntryTemplateModelTest(TestCase):
    """Test TimeEntryTemplate model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )

    def test_template_creation(self):
        """Test template creation."""
        template = TimeEntryTemplate.objects.create(
            user=self.user,
            workspace=self.workspace,
            name='Test Template',
            description='Test template description',
            template_data={
                'description': 'Default description',
                'is_billable': True,
                'hourly_rate': 50.00
            }
        )

        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.user, self.user)
        self.assertEqual(template.workspace, self.workspace)
        self.assertEqual(template.usage_count, 0)
        self.assertTrue(template.is_active)

    def test_template_str(self):
        """Test template string representation."""
        template = TimeEntryTemplate.objects.create(
            user=self.user,
            workspace=self.workspace,
            name='Test Template',
            description='Test template description',
            template_data={}
        )

        expected = f"{self.user.get_full_name()}: Test Template"
        self.assertEqual(str(template), expected)


class TimeEntryAPITest(APITestCase):
    """Test TimeEntry API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.organization.users.add(self.user)
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            key='TEST',
            created_by=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            reporter=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_time_entry(self):
        """Test creating a time entry via API."""
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)

        data = {
            'task': str(self.task.id),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'description': 'Test time entry'
        }

        response = self.client.post('/api/v1/time-entries/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Test time entry')
        self.assertEqual(response.data['duration_minutes'], 60)

    def test_list_time_entries(self):
        """Test listing time entries."""
        # Create a time entry
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)

        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=start_time,
            end_time=end_time
        )

        response = self.client.get('/api/v1/time-entries/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class TimerAPITest(APITestCase):
    """Test Timer API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            created_by=self.user
        )
        self.organization.users.add(self.user)
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            key='TEST',
            created_by=self.user
        )
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            reporter=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_timer(self):
        """Test creating a timer via API."""
        data = {
            'task': str(self.task.id),
            'description': 'Test timer'
        }

        response = self.client.post('/api/v1/timers/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Test timer')
        self.assertEqual(response.data['status'], 'running')

    def test_timer_control(self):
        """Test timer control actions."""
        # Create timer
        timer = Timer.objects.create(
            user=self.user,
            workspace=self.workspace,
            task=self.task,
            start_time=timezone.now(),
            description='Test timer'
        )

        # Pause timer
        data = {'action': 'pause'}
        response = self.client.post(
            f'/api/v1/timers/{timer.id}/control/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['timer']['status'], 'paused')


# Pytest-style tests
@pytest.mark.django_db
def test_time_entry_serializer():
    """Test TimeEntrySerializer."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    org = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=org,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        workspace=workspace,
        name='Test Project',
        key='TEST',
        created_by=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        reporter=user
    )

    start_time = timezone.now()
    end_time = start_time + timedelta(hours=2)

    time_entry = TimeEntry.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        start_time=start_time,
        end_time=end_time,
        description='Test time entry'
    )

    serializer = TimeEntrySerializer(time_entry)
    data = serializer.data

    assert data['description'] == 'Test time entry'
    assert data['duration_minutes'] == 120
    assert 'duration_display' in data
    assert 'cost_display' in data
    assert 'is_running' in data


@pytest.mark.django_db
def test_timer_serializer():
    """Test TimerSerializer."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    org = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=org,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        workspace=workspace,
        name='Test Project',
        key='TEST',
        created_by=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        reporter=user
    )

    start_time = timezone.now()

    timer = Timer.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        start_time=start_time,
        description='Test timer'
    )

    serializer = TimerSerializer(timer)
    data = serializer.data

    assert data['description'] == 'Test timer'
    assert data['status'] == 'running'
    assert 'current_duration_minutes' in data
    assert 'current_duration_display' in data


@pytest.mark.django_db
def test_timer_workflow():
    """Test complete timer workflow."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    org = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=org,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        workspace=workspace,
        name='Test Project',
        key='TEST',
        created_by=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        reporter=user
    )

    start_time = timezone.now()

    # Create timer
    timer = Timer.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        start_time=start_time,
        description='Test timer'
    )

    assert timer.status == 'running'

    # Pause timer
    timer.pause()
    assert timer.status == 'paused'

    # Resume timer
    timer.resume()
    assert timer.status == 'running'

    # Stop timer and create time entry
    end_time = start_time + timedelta(hours=1, minutes=30)
    time_entry = timer.stop(end_time)

    assert timer.status == 'stopped'
    assert time_entry is not None
    assert time_entry.duration_minutes == 90
    assert time_entry.description == 'Test timer'


@pytest.mark.django_db
def test_idle_period_tracking():
    """Test idle period tracking."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    org = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=org,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        workspace=workspace,
        name='Test Project',
        key='TEST',
        created_by=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        reporter=user
    )

    start_time = timezone.now()
    end_time = start_time + timedelta(hours=2)

    time_entry = TimeEntry.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        start_time=start_time,
        end_time=end_time
    )

    # Create idle period
    idle_start = start_time + timedelta(minutes=30)
    idle_end = idle_start + timedelta(minutes=10)

    idle_period = IdlePeriod.objects.create(
        time_entry=time_entry,
        start_time=idle_start,
        end_time=idle_end,
        detection_method='system'
    )

    assert idle_period.duration_minutes == 10
    assert idle_period in time_entry.idle_periods.all()


@pytest.mark.django_db
def test_time_entry_approval_workflow():
    """Test time entry approval workflow."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    approver = User.objects.create_user(
        username='approver',
        email='approver@example.com',
        password='testpass123'
    )
    org = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=org,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    project = Project.objects.create(
        workspace=workspace,
        name='Test Project',
        key='TEST',
        created_by=user
    )
    task = Task.objects.create(
        project=project,
        title='Test Task',
        reporter=user
    )

    start_time = timezone.now()
    end_time = start_time + timedelta(hours=1)

    time_entry = TimeEntry.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        start_time=start_time,
        end_time=end_time
    )

    # Initially not approved
    assert time_entry.is_approved is None

    # Approve
    time_entry.approve(approver, 'Great work!')
    assert time_entry.is_approved is True
    assert time_entry.approved_by == approver
    assert time_entry.approval_notes == 'Great work!'

    # Reject
    time_entry.reject(approver, 'Needs improvement')
    assert time_entry.is_approved is False
    assert time_entry.approval_notes == 'Needs improvement'