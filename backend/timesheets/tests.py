"""
Tests for timesheets app.

This module contains comprehensive tests for the timesheets app,
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
from time_entries.models import TimeEntry
from tasks.models import Project, Task
from .models import (
    TimesheetPeriod, Timesheet, TimesheetEntry, ApprovalWorkflow,
    TimesheetComment, TimesheetTemplate
)
from .serializers import (
    TimesheetPeriodSerializer, TimesheetSerializer, TimesheetEntrySerializer,
    ApprovalWorkflowSerializer, TimesheetCommentSerializer,
    TimesheetTemplateSerializer
)

User = get_user_model()


class TimesheetPeriodModelTest(TestCase):
    """Test TimesheetPeriod model."""

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

    def test_timesheet_period_creation(self):
        """Test timesheet period creation."""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=6)

        period = TimesheetPeriod.objects.create(
            workspace=self.workspace,
            name='Test Period',
            period_type='weekly',
            start_date=start_date,
            end_date=end_date,
            created_by=self.user
        )

        self.assertEqual(period.name, 'Test Period')
        self.assertEqual(period.workspace, self.workspace)
        self.assertEqual(period.period_type, 'weekly')
        self.assertTrue(period.is_active)

    def test_is_submission_open(self):
        """Test is_submission_open method."""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=6)

        period = TimesheetPeriod.objects.create(
            workspace=self.workspace,
            name='Test Period',
            start_date=start_date,
            end_date=end_date,
            created_by=self.user
        )

        # Should be open during the period
        self.assertTrue(period.is_submission_open())

        # Create overdue period
        overdue_period = TimesheetPeriod.objects.create(
            workspace=self.workspace,
            name='Overdue Period',
            start_date=start_date - timedelta(days=10),
            end_date=start_date - timedelta(days=3),
            created_by=self.user
        )

        self.assertFalse(overdue_period.is_submission_open())
        self.assertTrue(overdue_period.is_overdue())


class TimesheetModelTest(TestCase):
    """Test Timesheet model."""

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
        self.period = TimesheetPeriod.objects.create(
            workspace=self.workspace,
            name='Test Period',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6),
            created_by=self.user
        )

    def test_timesheet_creation(self):
        """Test timesheet creation."""
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period,
            title='Test Timesheet'
        )

        self.assertEqual(timesheet.title, 'Test Timesheet')
        self.assertEqual(timesheet.user, self.user)
        self.assertEqual(timesheet.workspace, self.workspace)
        self.assertEqual(timesheet.period, self.period)
        self.assertEqual(timesheet.status, 'draft')

    def test_timesheet_str(self):
        """Test timesheet string representation."""
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period
        )

        expected = f"{self.user.get_full_name()}: {self.period.start_date} - {self.period.end_date} (draft)"
        self.assertEqual(str(timesheet), expected)

    def test_submit_timesheet(self):
        """Test submit timesheet method."""
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period
        )

        timesheet.submit()

        self.assertEqual(timesheet.status, 'submitted')
        self.assertIsNotNone(timesheet.submitted_at)

    def test_approve_timesheet(self):
        """Test approve timesheet method."""
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period,
            status='submitted'
        )

        timesheet.approve(self.user)

        self.assertEqual(timesheet.status, 'approved')
        self.assertEqual(timesheet.approved_by, self.user)
        self.assertIsNotNone(timesheet.approved_at)


class TimesheetAPITest(APITestCase):
    """Test Timesheet API endpoints."""

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
        self.period = TimesheetPeriod.objects.create(
            workspace=self.workspace,
            name='Test Period',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6),
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_timesheet(self):
        """Test creating a timesheet via API."""
        data = {
            'period': str(self.period.id),
            'title': 'Test Timesheet'
        }

        response = self.client.post('/api/v1/timesheets/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Timesheet')
        self.assertEqual(response.data['status'], 'draft')

    def test_timesheet_transition(self):
        """Test timesheet status transition."""
        # Create timesheet
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period
        )

        # Submit timesheet
        data = {'status': 'submitted'}
        response = self.client.post(
            f'/api/v1/timesheets/{timesheet.id}/transition/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'submitted')

    def test_list_timesheets(self):
        """Test listing timesheets."""
        # Create timesheet
        Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period=self.period
        )

        response = self.client.get('/api/v1/timesheets/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class TimesheetPeriodAPITest(APITestCase):
    """Test TimesheetPeriod API endpoints."""

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
        self.client.force_authenticate(user=self.user)

    def test_create_timesheet_period(self):
        """Test creating a timesheet period via API."""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=6)

        data = {
            'name': 'Test Period',
            'period_type': 'weekly',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        response = self.client.post('/api/v1/timesheet-periods/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Period')
        self.assertEqual(response.data['period_type'], 'weekly')


# Pytest-style tests
@pytest.mark.django_db
def test_timesheet_period_serializer():
    """Test TimesheetPeriodSerializer."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )

    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=6)

    period = TimesheetPeriod.objects.create(
        workspace=workspace,
        name='Test Period',
        start_date=start_date,
        end_date=end_date,
        created_by=user
    )

    serializer = TimesheetPeriodSerializer(period)
    data = serializer.data

    assert data['name'] == 'Test Period'
    assert data['period_type'] == 'weekly'
    assert 'is_submission_open' in data
    assert 'completion_percentage' in data


@pytest.mark.django_db
def test_timesheet_serializer():
    """Test TimesheetSerializer."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    period = TimesheetPeriod.objects.create(
        workspace=workspace,
        name='Test Period',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=6),
        created_by=user
    )

    timesheet = Timesheet.objects.create(
        user=user,
        workspace=workspace,
        period=period,
        title='Test Timesheet'
    )

    serializer = TimesheetSerializer(timesheet)
    data = serializer.data

    assert data['title'] == 'Test Timesheet'
    assert data['status'] == 'draft'
    assert 'completion_percentage' in data
    assert 'entries_count' in data


@pytest.mark.django_db
def test_timesheet_workflow():
    """Test complete timesheet workflow."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    period = TimesheetPeriod.objects.create(
        workspace=workspace,
        name='Test Period',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=6),
        created_by=user
    )

    # Create timesheet
    timesheet = Timesheet.objects.create(
        user=user,
        workspace=workspace,
        period=period
    )

    # Submit timesheet
    timesheet.submit()
    assert timesheet.status == 'submitted'

    # Approve timesheet
    timesheet.approve(user)
    assert timesheet.status == 'approved'
    assert timesheet.approved_by == user


@pytest.mark.django_db
def test_timesheet_entry_creation():
    """Test timesheet entry creation and management."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )
    period = TimesheetPeriod.objects.create(
        workspace=workspace,
        name='Test Period',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=6),
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

    # Create timesheet
    timesheet = Timesheet.objects.create(
        user=user,
        workspace=workspace,
        period=period
    )

    # Create time entry
    start_time = timezone.now()
    end_time = start_time + timedelta(hours=2)
    time_entry = TimeEntry.objects.create(
        user=user,
        workspace=workspace,
        task=task,
        project=project,
        start_time=start_time,
        end_time=end_time
    )

    # Create timesheet entry
    timesheet_entry = TimesheetEntry.objects.create(
        timesheet=timesheet,
        time_entry=time_entry
    )

    assert timesheet_entry.timesheet == timesheet
    assert timesheet_entry.time_entry == time_entry
    assert timesheet_entry.get_effective_hours() == 2.0


@pytest.mark.django_db
def test_approval_workflow():
    """Test approval workflow functionality."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    organization = Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        created_by=user
    )
    workspace = Workspace.objects.create(
        organization=organization,
        name='Test Workspace',
        slug='test-workspace',
        created_by=user
    )

    # Create approval workflow
    workflow = ApprovalWorkflow.objects.create(
        workspace=workspace,
        name='Test Workflow',
        workflow_type='sequential',
        steps=[
            {
                'step': 1,
                'approver_role': 'manager',
                'approver_user': None,
                'conditions': []
            }
        ],
        created_by=user
    )

    assert workflow.name == 'Test Workflow'
    assert workflow.workflow_type == 'sequential'
    assert len(workflow.steps) == 1