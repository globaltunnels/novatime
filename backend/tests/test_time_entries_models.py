import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from time_entries.models import TimeEntry

User = get_user_model()


class TimeEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for TimeEntry)
        from organizations.models import Organization, Workspace
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            slug='test-workspace'
        )
        
        # Create project (required for TimeEntry)
        from projects.models import Project
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project'
        )
        
    def test_time_entry_creation(self):
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=1)
        
        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time(),
            description='Test time entry'
        )
        
        self.assertEqual(time_entry.user, self.user)
        self.assertEqual(time_entry.workspace, self.workspace)
        self.assertEqual(time_entry.project, self.project)
        self.assertEqual(time_entry.date, start_time.date())
        self.assertEqual(time_entry.start_time, start_time.time())
        self.assertEqual(time_entry.end_time, end_time.time())
        self.assertEqual(time_entry.description, 'Test time entry')
        self.assertEqual(time_entry.source, 'manual')
        self.assertIsNotNone(time_entry.created_at)
        self.assertIsNotNone(time_entry.updated_at)
        
    def test_time_entry_string_representation(self):
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=1)
        
        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time(),
            description='Test time entry'
        )
        
        expected_str = f"{self.user.username} - {time_entry.date}: {time_entry.duration} hours"
        self.assertEqual(str(time_entry), expected_str)
        
    def test_time_entry_duration_property(self):
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=2, minutes=30)
        
        time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time()
        )
        
        self.assertEqual(time_entry.duration, 2.5)