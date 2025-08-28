"""
Tests for time_entries app.

This module contains comprehensive tests for the time_entries app,
including model tests, serializer tests, and view tests.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from .models import (
    TimeEntry, Timer, TimeEntryApproval, IdlePeriod, TimeEntryTemplate,
    TimeEntryCategory, TimeEntryTag, TimeEntryComment, TimeEntryAttachment
)
from .serializers import (
    TimeEntrySerializer, TimeEntryCreateSerializer, TimerSerializer,
    TimerCreateSerializer, TimeEntryApprovalSerializer,
    TimeEntryApprovalCreateSerializer, IdlePeriodSerializer,
    TimeEntryTemplateSerializer, TimeEntryCategorySerializer,
    TimeEntryTagSerializer, TimeEntryCommentSerializer,
    TimeEntryAttachmentSerializer
)

User = get_user_model()


class TimeEntryModelTest(TestCase):
    """Test TimeEntry model."""

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
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            created_by=self.user
        )
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            duration_minutes=60,
            description='Test time entry',
            is_billable=True,
            hourly_rate=Decimal('50.00')
        )

    def test_time_entry_creation(self):
        """Test time entry creation."""
        self.assertEqual(self.time_entry.user, self.user)
        self.assertEqual(self.time_entry.organization, self.organization)
        self.assertEqual(self.time_entry.workspace, self.workspace)
        self.assertEqual(self.time_entry.project, self.project)
        self.assertEqual(self.time_entry.task, self.task)
        self.assertEqual(self.time_entry.duration_minutes, 60)
        self.assertEqual(self.time_entry.description, 'Test time entry')
        self.assertTrue(self.time_entry.is_billable)
        self.assertEqual(self.time_entry.hourly_rate, Decimal('50.00'))
        self.assertEqual(self.time_entry.status, 'draft')
        self.assertEqual(self.time_entry.entry_type, 'manual')

    def test_time_entry_str(self):
        """Test time entry string representation."""
        expected = 'Test User: Test Task (60min)'
        self.assertEqual(str(self.time_entry), expected)

    def test_time_entry_cost_calculation(self):
        """Test time entry cost calculation."""
        expected_cost = Decimal('50.00')  # 1 hour * $50/hour
        self.assertEqual(self.time_entry.get_cost(), expected_cost)
        self.assertEqual(self.time_entry.cost_amount, expected_cost)

    def test_time_entry_duration_hours(self):
        """Test time entry duration in hours."""
        self.assertEqual(self.time_entry.get_duration_hours(), Decimal('1.00'))

    def test_time_entry_permissions(self):
        """Test time entry permissions."""
        # Owner should have edit permission
        self.assertTrue(self.time_entry.can_user_edit(self.user))

        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Other user should not have edit permission
        self.assertFalse(self.time_entry.can_user_edit(other_user))

        # Add other user to workspace
        self.workspace.add_member(other_user, 'member')

        # Other user should have edit permission
        self.assertTrue(self.time_entry.can_user_edit(other_user))

    def test_time_entry_approval_workflow(self):
        """Test time entry approval workflow."""
        # Submit for approval
        self.time_entry.submit_for_approval()
        self.assertEqual(self.time_entry.status, 'submitted')
        self.assertIsNotNone(self.time_entry.submitted_at)

        # Approve
        self.time_entry.approve(self.user)
        self.assertEqual(self.time_entry.status, 'approved')
        self.assertIsNotNone(self.time_entry.approved_at)
        self.assertEqual(self.time_entry.approved_by, self.user)

        # Reject
        self.time_entry.reject('Test rejection')
        self.assertEqual(self.time_entry.status, 'rejected')
        self.assertEqual(self.time_entry.rejection_reason, 'Test rejection')

        # Lock
        self.time_entry.lock()
        self.assertEqual(self.time_entry.status, 'locked')

    def test_time_entry_running_status(self):
        """Test time entry running status."""
        # Entry with end time is not running
        self.assertFalse(self.time_entry.is_running())

        # Create running entry
        running_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            start_time=timezone.now(),
            duration_minutes=0
        )
        self.assertTrue(running_entry.is_running())


class TimerModelTest(TestCase):
    """Test Timer model."""

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
        self.timer = Timer.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            description='Test timer',
            is_billable=True,
            hourly_rate=Decimal('50.00')
        )

    def test_timer_creation(self):
        """Test timer creation."""
        self.assertEqual(self.timer.user, self.user)
        self.assertEqual(self.timer.organization, self.organization)
        self.assertEqual(self.timer.workspace, self.workspace)
        self.assertEqual(self.timer.project, self.project)
        self.assertEqual(self.timer.task, self.task)
        self.assertEqual(self.timer.description, 'Test timer')
        self.assertTrue(self.timer.is_billable)
        self.assertEqual(self.timer.hourly_rate, Decimal('50.00'))
        self.assertEqual(self.timer.status, 'running')
        self.assertIsNotNone(self.timer.start_time)

    def test_timer_str(self):
        """Test timer string representation."""
        expected = 'Test User: Test Task (00:00:00)'
        self.assertEqual(str(self.timer), expected)

    def test_timer_elapsed_time(self):
        """Test timer elapsed time calculation."""
        # Stop the timer after 1 hour
        self.timer.end_time = self.timer.start_time + timedelta(hours=1)
        self.timer.status = 'stopped'
        self.timer.save()

        self.assertEqual(self.timer.get_elapsed_time(), '01:00:00')
        self.assertEqual(self.timer.get_elapsed_seconds(), 3600)
        self.assertEqual(self.timer.get_elapsed_minutes(), 60)

    def test_timer_workflow(self):
        """Test timer workflow."""
        # Initially running
        self.assertEqual(self.timer.status, 'running')

        # Pause
        self.timer.pause()
        self.assertEqual(self.timer.status, 'paused')
        self.assertIsNotNone(self.timer.paused_at)

        # Resume
        self.timer.resume()
        self.assertEqual(self.timer.status, 'running')
        self.assertIsNone(self.timer.paused_at)

        # Stop
        time_entry = self.timer.stop()
        self.assertEqual(self.timer.status, 'stopped')
        self.assertIsNotNone(self.timer.end_time)
        self.assertIsNotNone(time_entry)
        self.assertEqual(time_entry.entry_type, 'timer')

    def test_timer_idle_detection(self):
        """Test timer idle detection."""
        # Timer should not be idle initially
        self.assertFalse(self.timer.is_idle())

        # Set last activity to 10 minutes ago
        self.timer.last_activity_at = timezone.now() - timedelta(minutes=10)
        self.timer.save()

        # Timer should be idle
        self.assertTrue(self.timer.is_idle())

        # Handle idle
        self.timer.handle_idle()
        self.assertEqual(self.timer.status, 'paused')

    def test_timer_create_time_entry(self):
        """Test timer creating time entry."""
        # Stop timer
        self.timer.end_time = self.timer.start_time + timedelta(hours=1)
        self.timer.status = 'stopped'
        self.timer.save()

        # Create time entry
        time_entry = self.timer.create_time_entry()

        self.assertIsNotNone(time_entry)
        self.assertEqual(time_entry.user, self.timer.user)
        self.assertEqual(time_entry.project, self.timer.project)
        self.assertEqual(time_entry.task, self.timer.task)
        self.assertEqual(time_entry.duration_minutes, 60)
        self.assertEqual(time_entry.entry_type, 'timer')


class TimeEntryApprovalModelTest(TestCase):
    """Test TimeEntryApproval model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.approver = User.objects.create_user(
            email='approver@example.com',
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
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            duration_minutes=60,
            description='Test time entry'
        )
        self.approval = TimeEntryApproval.objects.create(
            organization=self.organization,
            workspace=self.workspace,
            approver=self.approver,
            requested_by=self.user,
            approval_type='weekly',
            period_start=timezone.now().date(),
            period_end=timezone.now().date() + timedelta(days=6)
        )
        self.approval.time_entries.add(self.time_entry)

    def test_approval_creation(self):
        """Test approval creation."""
        self.assertEqual(self.approval.organization, self.organization)
        self.assertEqual(self.approval.workspace, self.workspace)
        self.assertEqual(self.approval.approver, self.approver)
        self.assertEqual(self.approval.requested_by, self.user)
        self.assertEqual(self.approval.approval_type, 'weekly')
        self.assertEqual(self.approval.status, 'pending')
        self.assertIsNotNone(self.approval.requested_at)

    def test_approval_str(self):
        """Test approval string representation."""
        expected = f"Approval for {self.user.get_full_name()}: {self.approval.period_start} - {self.approval.period_end}"
        self.assertEqual(str(self.approval), expected)

    def test_approval_workflow(self):
        """Test approval workflow."""
        # Approve
        self.approval.approve('Approved via test')
        self.assertEqual(self.approval.status, 'approved')
        self.assertIsNotNone(self.approval.responded_at)
        self.assertEqual(self.time_entry.status, 'approved')

        # Reject
        self.approval.reject('Rejected via test')
        self.assertEqual(self.approval.status, 'rejected')
        self.assertEqual(self.time_entry.status, 'rejected')


class IdlePeriodModelTest(TestCase):
    """Test IdlePeriod model."""

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
        self.timer = Timer.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            description='Test timer'
        )
        self.idle_period = IdlePeriod.objects.create(
            user=self.user,
            timer=self.timer,
            start_time=timezone.now(),
            duration_seconds=300,
            reason='user_inactive'
        )

    def test_idle_period_creation(self):
        """Test idle period creation."""
        self.assertEqual(self.idle_period.user, self.user)
        self.assertEqual(self.idle_period.timer, self.timer)
        self.assertEqual(self.idle_period.duration_seconds, 300)
        self.assertEqual(self.idle_period.reason, 'user_inactive')
        self.assertEqual(self.idle_period.action_taken, 'none')

    def test_idle_period_str(self):
        """Test idle period string representation."""
        expected = 'Test User: Idle (300s) - user_inactive'
        self.assertEqual(str(self.idle_period), expected)

    def test_idle_period_duration_minutes(self):
        """Test idle period duration in minutes."""
        self.assertEqual(self.idle_period.get_duration_minutes(), 5)

    def test_idle_period_active_status(self):
        """Test idle period active status."""
        # Initially not active (has end_time)
        self.assertFalse(self.idle_period.is_active())

        # Create active idle period
        active_idle = IdlePeriod.objects.create(
            user=self.user,
            timer=self.timer,
            start_time=timezone.now(),
            reason='user_inactive'
        )
        self.assertTrue(active_idle.is_active())

        # Stop it
        active_idle.stop()
        self.assertFalse(active_idle.is_active())


class TimeEntryTemplateModelTest(TestCase):
    """Test TimeEntryTemplate model."""

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
        self.template = TimeEntryTemplate.objects.create(
            name='Test Template',
            description='A test template',
            template_type='project',
            template_data={
                'description': 'Template description',
                'is_billable': True,
                'hourly_rate': 50.00,
                'tags': ['development', 'backend'],
                'categories': ['coding']
            },
            organization=self.organization,
            created_by=self.user
        )

    def test_template_creation(self):
        """Test template creation."""
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.description, 'A test template')
        self.assertEqual(self.template.template_type, 'project')
        self.assertEqual(self.template.usage_count, 0)
        self.assertTrue(self.template.is_public)
        self.assertFalse(self.template.is_system)

    def test_template_str(self):
        """Test template string representation."""
        expected = 'project: Test Template'
        self.assertEqual(str(self.template), expected)

    def test_template_usage_increment(self):
        """Test template usage increment."""
        self.template.increment_usage()
        self.assertEqual(self.template.usage_count, 1)


class TimeEntryCategoryModelTest(TestCase):
    """Test TimeEntryCategory model."""

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
        self.category = TimeEntryCategory.objects.create(
            name='Development',
            description='Development work',
            color='#2563EB',
            organization=self.organization,
            created_by=self.user
        )

    def test_category_creation(self):
        """Test category creation."""
        self.assertEqual(self.category.name, 'Development')
        self.assertEqual(self.category.description, 'Development work')
        self.assertEqual(self.category.color, '#2563EB')
        self.assertEqual(self.category.usage_count, 0)

    def test_category_str(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), 'Test Organization: Development')

    def test_category_usage_increment(self):
        """Test category usage increment."""
        self.category.increment_usage()
        self.assertEqual(self.category.usage_count, 1)


class TimeEntryTagModelTest(TestCase):
    """Test TimeEntryTag model."""

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
        self.tag = TimeEntryTag.objects.create(
            name='urgent',
            description='Urgent tasks',
            color='#EF4444',
            organization=self.organization,
            created_by=self.user
        )

    def test_tag_creation(self):
        """Test tag creation."""
        self.assertEqual(self.tag.name, 'urgent')
        self.assertEqual(self.tag.description, 'Urgent tasks')
        self.assertEqual(self.tag.color, '#EF4444')
        self.assertEqual(self.tag.usage_count, 0)

    def test_tag_str(self):
        """Test tag string representation."""
        self.assertEqual(str(self.tag), 'Test Organization: urgent')

    def test_tag_usage_increment(self):
        """Test tag usage increment."""
        self.tag.increment_usage()
        self.assertEqual(self.tag.usage_count, 1)


class TimeEntryCommentModelTest(TestCase):
    """Test TimeEntryComment model."""

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
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            duration_minutes=60,
            description='Test time entry'
        )
        self.comment = TimeEntryComment.objects.create(
            time_entry=self.time_entry,
            author=self.user,
            content='This is a test comment'
        )

    def test_comment_creation(self):
        """Test comment creation."""
        self.assertEqual(self.comment.time_entry, self.time_entry)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'This is a test comment')
        self.assertIsNone(self.comment.parent_comment)

    def test_comment_str(self):
        """Test comment string representation."""
        expected = 'Test User: This is a test comment...'
        self.assertEqual(str(self.comment), expected)

    def test_comment_replies(self):
        """Test comment replies."""
        reply = TimeEntryComment.objects.create(
            time_entry=self.time_entry,
            author=self.user,
            content='This is a reply',
            parent_comment=self.comment
        )

        self.assertIn(reply, self.comment.replies.all())
        self.assertEqual(reply.parent_comment, self.comment)


class TimeEntryAttachmentModelTest(TestCase):
    """Test TimeEntryAttachment model."""

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
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            duration_minutes=60,
            description='Test time entry'
        )
        self.attachment = TimeEntryAttachment.objects.create(
            time_entry=self.time_entry,
            uploaded_by=self.user,
            filename='test.txt',
            file_size=1024,
            content_type='text/plain'
        )

    def test_attachment_creation(self):
        """Test attachment creation."""
        self.assertEqual(self.attachment.time_entry, self.time_entry)
        self.assertEqual(self.attachment.uploaded_by, self.user)
        self.assertEqual(self.attachment.filename, 'test.txt')
        self.assertEqual(self.attachment.file_size, 1024)
        self.assertEqual(self.attachment.content_type, 'text/plain')

    def test_attachment_str(self):
        """Test attachment string representation."""
        expected = 'Test Project: Test Task: test.txt'
        self.assertEqual(str(self.attachment), expected)


# Pytest-style tests
@pytest.mark.django_db
def test_time_entry_serializer():
    """Test TimeEntrySerializer."""
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
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry'
    )

    serializer = TimeEntrySerializer(time_entry)
    data = serializer.data

    assert data['description'] == 'Test time entry'
    assert data['duration_minutes'] == 60
    assert data['status'] == 'draft'
    assert data['can_user_edit'] is True
    assert data['cost_amount'] == 0


@pytest.mark.django_db
def test_timer_serializer():
    """Test TimerSerializer."""
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
    timer = Timer.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        description='Test timer'
    )

    serializer = TimerSerializer(timer)
    data = serializer.data

    assert data['description'] == 'Test timer'
    assert data['status'] == 'running'
    assert data['elapsed_time'] == '00:00:00'
    assert data['is_idle'] is False


@pytest.mark.django_db
def test_time_entry_approval_serializer():
    """Test TimeEntryApprovalSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    approver = User.objects.create_user(
        email='approver@example.com',
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
    approval = TimeEntryApproval.objects.create(
        organization=organization,
        workspace=workspace,
        approver=approver,
        requested_by=user,
        approval_type='weekly',
        period_start=timezone.now().date(),
        period_end=timezone.now().date() + timedelta(days=6)
    )

    serializer = TimeEntryApprovalSerializer(approval)
    data = serializer.data

    assert data['approval_type'] == 'weekly'
    assert data['status'] == 'pending'
    assert data['total_hours'] == 0
    assert data['total_entries'] == 0


@pytest.mark.django_db
def test_idle_period_serializer():
    """Test IdlePeriodSerializer."""
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
    timer = Timer.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        description='Test timer'
    )
    idle_period = IdlePeriod.objects.create(
        user=user,
        timer=timer,
        start_time=timezone.now(),
        duration_seconds=300,
        reason='user_inactive'
    )

    serializer = IdlePeriodSerializer(idle_period)
    data = serializer.data

    assert data['duration_seconds'] == 300
    assert data['reason'] == 'user_inactive'
    assert data['is_active'] is False


@pytest.mark.django_db
def test_time_entry_template_serializer():
    """Test TimeEntryTemplateSerializer."""
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
    template = TimeEntryTemplate.objects.create(
        name='Test Template',
        template_type='project',
        template_data={'key': 'value'},
        organization=organization,
        created_by=user
    )

    serializer = TimeEntryTemplateSerializer(template)
    data = serializer.data

    assert data['name'] == 'Test Template'
    assert data['template_type'] == 'project'
    assert data['template_data'] == {'key': 'value'}
    assert data['usage_count'] == 0


@pytest.mark.django_db
def test_time_entry_category_serializer():
    """Test TimeEntryCategorySerializer."""
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
    category = TimeEntryCategory.objects.create(
        name='Development',
        organization=organization,
        created_by=user
    )

    serializer = TimeEntryCategorySerializer(category)
    data = serializer.data

    assert data['name'] == 'Development'
    assert data['usage_count'] == 0


@pytest.mark.django_db
def test_time_entry_tag_serializer():
    """Test TimeEntryTagSerializer."""
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
    tag = TimeEntryTag.objects.create(
        name='urgent',
        organization=organization,
        created_by=user
    )

    serializer = TimeEntryTagSerializer(tag)
    data = serializer.data

    assert data['name'] == 'urgent'
    assert data['usage_count'] == 0


@pytest.mark.django_db
def test_time_entry_comment_serializer():
    """Test TimeEntryCommentSerializer."""
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
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry'
    )
    comment = TimeEntryComment.objects.create(
        time_entry=time_entry,
        author=user,
        content='This is a test comment'
    )

    serializer = TimeEntryCommentSerializer(comment)
    data = serializer.data

    assert data['content'] == 'This is a test comment'
    assert data['replies_count'] == 0
    assert data['replies'] == []


@pytest.mark.django_db
def test_time_entry_attachment_serializer():
    """Test TimeEntryAttachmentSerializer."""
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
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry'
    )
    attachment = TimeEntryAttachment.objects.create(
        time_entry=time_entry,
        uploaded_by=user,
        filename='test.txt',
        file_size=1024,
        content_type='text/plain'
    )

    serializer = TimeEntryAttachmentSerializer(attachment)
    data = serializer.data

    assert data['filename'] == 'test.txt'
    assert data['file_size'] == 1024
    assert data['content_type'] == 'text/plain'


@pytest.mark.django_db
def test_time_entry_workflow():
    """Test complete time entry workflow."""
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

    # Create time entry
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry',
        is_billable=True,
        hourly_rate=Decimal('50.00')
    )

    assert time_entry.status == 'draft'
    assert time_entry.cost_amount == Decimal('50.00')

    # Submit for approval
    time_entry.submit_for_approval()
    assert time_entry.status == 'submitted'

    # Approve
    approver = User.objects.create_user(
        email='approver@example.com',
        password='testpass123'
    )
    workspace.add_member(approver, 'admin')

    time_entry.approve(approver)
    assert time_entry.status == 'approved'

    # Lock
    time_entry.lock()
    assert time_entry.status == 'locked'


@pytest.mark.django_db
def test_timer_workflow():
    """Test complete timer workflow."""
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

    # Create timer
    timer = Timer.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        description='Test timer',
        is_billable=True,
        hourly_rate=Decimal('50.00')
    )

    assert timer.status == 'running'

    # Pause
    timer.pause()
    assert timer.status == 'paused'

    # Resume
    timer.resume()
    assert timer.status == 'running'

    # Stop and create time entry
    time_entry = timer.stop()
    assert timer.status == 'stopped'
    assert time_entry is not None
    assert time_entry.entry_type == 'timer'


@pytest.mark.django_db
def test_approval_workflow():
    """Test complete approval workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    approver = User.objects.create_user(
        email='approver@example.com',
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
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry'
    )

    # Create approval
    approval = TimeEntryApproval.objects.create(
        organization=organization,
        workspace=workspace,
        approver=approver,
        requested_by=user,
        approval_type='weekly',
        period_start=timezone.now().date(),
        period_end=timezone.now().date() + timedelta(days=6)
    )
    approval.time_entries.add(time_entry)

    assert approval.status == 'pending'

    # Approve
    approval.approve('Approved via test')
    assert approval.status == 'approved'
    time_entry.refresh_from_db()
    assert time_entry.status == 'approved'

    # Reject
    approval.reject('Rejected via test')
    assert approval.status == 'rejected'
    time_entry.refresh_from_db()
    assert time_entry.status == 'rejected'


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
        'description': 'Template description',
        'is_billable': True,
        'hourly_rate': 50.00,
        'tags': ['development', 'backend'],
        'categories': ['coding']
    }

    template = TimeEntryTemplate.objects.create(
        name='Test Template',
        description='A test template',
        template_type='project',
        template_data=template_data,
        organization=organization,
        created_by=user
    )

    assert template.usage_count == 0

    # Apply template
    time_entry = template.create_time_entry(user)
    assert time_entry is not None
    assert time_entry.description == 'Template description'
    assert time_entry.is_billable is True
    assert time_entry.hourly_rate == Decimal('50.00')
    assert template.usage_count == 1


@pytest.mark.django_db
def test_idle_period_workflow():
    """Test complete idle period workflow."""
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
    timer = Timer.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        description='Test timer'
    )

    # Create idle period
    idle_period = IdlePeriod.objects.create(
        user=user,
        timer=timer,
        start_time=timezone.now(),
        reason='user_inactive'
    )

    assert idle_period.is_active() is True
    assert idle_period.action_taken == 'none'

    # Stop idle period
    idle_period.stop()
    assert idle_period.is_active() is False
    assert idle_period.duration_seconds > 0


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
    time_entry = TimeEntry.objects.create(
        user=user,
        organization=organization,
        workspace=workspace,
        project=project,
        task=task,
        start_time=timezone.now(),
        duration_minutes=60,
        description='Test time entry'
    )

    # Create comment
    comment = TimeEntryComment.objects.create(
        time_entry=time_entry,
        author=user,
        content='This is a test comment'
    )

    assert comment.content == 'This is a test comment'

    # Create reply
    reply = TimeEntryComment.objects.create(
        time_entry=time_entry,
        author=user,
        content='This is a reply',
        parent_comment=comment
    )

    assert reply.parent_comment == comment
    assert reply in comment.replies.all()


@pytest.mark.django_db
def test_category_and_tag_workflow():
    """Test complete category and tag workflow."""
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

    # Create category
    category = TimeEntryCategory.objects.create(
        name='Development',
        organization=organization,
        created_by=user
    )

    assert category.usage_count == 0

    # Create tag
    tag = TimeEntryTag.objects.create(
        name='urgent',
        organization=organization,
        created_by=user
    )

    assert tag.usage_count == 0

    # Increment usage
    category.increment_usage()
    tag.increment_usage()

    assert category.usage_count == 1
    assert tag.usage_count == 1