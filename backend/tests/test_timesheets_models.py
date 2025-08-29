import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from timesheets.models import Timesheet, TimesheetEntry

User = get_user_model()


class TimesheetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for Timesheet)
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
        
    def test_timesheet_creation(self):
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=6)
        
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            period_type='weekly',
            start_date=start_date,
            end_date=end_date,
            status='draft'
        )
        
        self.assertEqual(timesheet.user, self.user)
        self.assertEqual(timesheet.workspace, self.workspace)
        self.assertEqual(timesheet.period_type, 'weekly')
        self.assertEqual(timesheet.start_date, start_date)
        self.assertEqual(timesheet.end_date, end_date)
        self.assertEqual(timesheet.status, 'draft')
        self.assertIsNotNone(timesheet.created_at)
        self.assertIsNotNone(timesheet.updated_at)
        
    def test_timesheet_string_representation(self):
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=6)
        
        timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            start_date=start_date,
            end_date=end_date
        )
        
        expected_str = f"{self.user.username} - {start_date} to {end_date}"
        self.assertEqual(str(timesheet), expected_str)


class TimesheetEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for Timesheet)
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
        
        self.timesheet = Timesheet.objects.create(
            user=self.user,
            workspace=self.workspace,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=6)
        )
        
        # Create project (required for TimesheetEntry)
        from projects.models import Project
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project'
        )
        
    def test_timesheet_entry_creation(self):
        entry = TimesheetEntry.objects.create(
            timesheet=self.timesheet,
            project=self.project,
            day='monday',
            hours=8.0,
            description='Work on project'
        )
        
        self.assertEqual(entry.timesheet, self.timesheet)
        self.assertEqual(entry.project, self.project)
        self.assertEqual(entry.day, 'monday')
        self.assertEqual(entry.hours, 8.0)
        self.assertEqual(entry.description, 'Work on project')
        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)
        
    def test_timesheet_entry_string_representation(self):
        entry = TimesheetEntry.objects.create(
            timesheet=self.timesheet,
            project=self.project,
            day='tuesday',
            hours=7.5
        )
        
        expected_str = f"Timesheet Entry for {entry.day}: {entry.hours} hours"
        self.assertEqual(str(entry), expected_str)