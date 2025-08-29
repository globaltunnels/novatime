import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from projects.models import Client, Project, ProjectMember
from projects.serializers import (
    ClientSerializer, ProjectMemberSerializer, ProjectSerializer,
    ProjectCreateSerializer, ProjectSummarySerializer, ProjectTimelineSerializer,
    ProjectMemberActionSerializer, ProjectStatsSerializer
)
from organizations.models import Organization, Workspace
from tasks.models import Task
from time_entries.models import TimeEntry

User = get_user_model()


class ClientSerializerTest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@example.com',
            phone='+1234567890',
            website='https://client.com',
            default_hourly_rate=Decimal('100.00'),
            currency='USD'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            billing_type='hourly',
            hourly_rate=Decimal('125.00')
        )

    def test_client_serialization(self):
        """Test Client serialization."""
        serializer = ClientSerializer(self.client_obj)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Client')
        self.assertEqual(data['email'], 'client@example.com')
        self.assertEqual(data['phone'], '+1234567890')
        self.assertEqual(data['website'], 'https://client.com')
        self.assertEqual(Decimal(data['default_hourly_rate']), Decimal('100.00'))
        self.assertEqual(data['currency'], 'USD')

    def test_client_projects_count(self):
        """Test projects count calculation."""
        serializer = ClientSerializer(self.client_obj)
        self.assertEqual(serializer.data['projects_count'], 1)

        # Create another project
        Project.objects.create(
            name='Another Project',
            workspace=self.workspace,
            client=self.client_obj,
            status='completed'
        )

        serializer = ClientSerializer(self.client_obj)
        self.assertEqual(serializer.data['projects_count'], 1)  # Only active projects

    def test_client_total_project_value(self):
        """Test total project value calculation."""
        # Set fixed price for project
        self.project.fixed_price = Decimal('5000.00')
        self.project.billing_type = 'fixed'
        self.project.save()

        serializer = ClientSerializer(self.client_obj)
        self.assertEqual(Decimal(serializer.data['total_project_value']), Decimal('5000.00'))

    def test_client_deserialization(self):
        """Test Client deserialization."""
        data = {
            'name': 'New Client',
            'email': 'newclient@example.com',
            'phone': '+0987654321',
            'default_hourly_rate': '150.00',
            'currency': 'EUR'
        }

        serializer = ClientSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        client = serializer.save()

        self.assertEqual(client.name, 'New Client')
        self.assertEqual(client.email, 'newclient@example.com')
        self.assertEqual(client.default_hourly_rate, Decimal('150.00'))


class ProjectMemberSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace
        )

        self.member = ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='developer',
            hourly_rate=Decimal('75.00'),
            allocation_percent=80
        )

    def test_project_member_serialization(self):
        """Test ProjectMember serialization."""
        serializer = ProjectMemberSerializer(self.member)
        data = serializer.data

        self.assertEqual(data['role'], 'developer')
        self.assertEqual(Decimal(data['hourly_rate']), Decimal('75.00'))
        self.assertEqual(data['allocation_percent'], 80)
        self.assertEqual(data['user_name'], 'Test User')
        self.assertEqual(data['user_email'], 'test@example.com')

    def test_allocation_percent_validation(self):
        """Test allocation percent validation."""
        # Valid allocation
        data = {'allocation_percent': 50}
        serializer = ProjectMemberSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid allocation - too low
        data = {'allocation_percent': 0}
        serializer = ProjectMemberSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Invalid allocation - too high
        data = {'allocation_percent': 150}
        serializer = ProjectMemberSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ProjectSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123',
            first_name='Project',
            last_name='Manager'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@example.com'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user,
            billing_type='hourly',
            hourly_rate=Decimal('100.00'),
            budget_hours=100,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        # Create some time entries
        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            duration_minutes=480,  # 8 hours
            is_billable=True
        )

        # Create some tasks
        Task.objects.create(
            project=self.project,
            title='Task 1',
            status='completed'
        )
        Task.objects.create(
            project=self.project,
            title='Task 2',
            status='in_progress'
        )

    def test_project_serialization(self):
        """Test Project serialization."""
        serializer = ProjectSerializer(self.project)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Project')
        self.assertEqual(data['description'], 'A test project')
        self.assertEqual(data['billing_type'], 'hourly')
        self.assertEqual(Decimal(data['hourly_rate']), Decimal('100.00'))
        self.assertEqual(data['client_name'], 'Test Client')
        self.assertEqual(data['manager_name'], 'Project Manager')
        self.assertEqual(data['workspace_name'], 'Test Workspace')

    def test_project_calculated_fields(self):
        """Test calculated fields in Project serializer."""
        serializer = ProjectSerializer(self.project)
        data = serializer.data

        # Test total hours (8 hours = 480 minutes)
        self.assertEqual(data['total_hours'], 8.0)

        # Test billable hours
        self.assertEqual(data['billable_hours'], 8.0)

        # Test total cost (8 hours * $100/hour)
        self.assertEqual(Decimal(data['total_cost']), Decimal('800.00'))

        # Test progress percentage (1 completed out of 2 tasks = 50%)
        self.assertEqual(data['progress_percentage'], 50.0)

        # Test team size
        self.assertEqual(data['team_size'], 0)  # No project members added

    def test_project_overdue_check(self):
        """Test overdue project detection."""
        # Set end date to yesterday
        self.project.end_date = date.today() - timedelta(days=1)
        self.project.save()

        serializer = ProjectSerializer(self.project)
        self.assertTrue(serializer.data['is_overdue'])

        # Set status to completed
        self.project.status = 'completed'
        self.project.save()

        serializer = ProjectSerializer(self.project)
        self.assertFalse(serializer.data['is_overdue'])

    def test_project_over_budget_check(self):
        """Test over budget detection."""
        # Add more time to go over budget
        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            duration_minutes=6000  # 100 hours
        )

        serializer = ProjectSerializer(self.project)
        self.assertTrue(serializer.data['is_over_budget'])

    def test_project_validation(self):
        """Test Project validation."""
        # Test end date before start date
        data = {
            'name': 'Invalid Project',
            'start_date': date.today(),
            'end_date': date.today() - timedelta(days=1)
        }

        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

        # Test hourly billing without rate
        data = {
            'name': 'Invalid Project',
            'billing_type': 'hourly'
            # Missing hourly_rate
        }

        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Test fixed price billing without price
        data = {
            'name': 'Invalid Project',
            'billing_type': 'fixed'
            # Missing fixed_price
        }

        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ProjectCreateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123'
        )

        self.client_obj = Client.objects.create(name='Test Client')

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

    def test_project_creation_with_members(self):
        """Test project creation with initial members."""
        data = {
            'name': 'New Project',
            'workspace': self.workspace.id,
            'client': self.client_obj.id,
            'manager': self.user.id,
            'billing_type': 'hourly',
            'hourly_rate': '120.00',
            'initial_members': [str(self.user.id)]
        }

        serializer = ProjectCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        project = serializer.save()

        self.assertEqual(project.name, 'New Project')
        self.assertEqual(project.members.count(), 1)
        self.assertEqual(project.members.first().user, self.user)


class ProjectSummarySerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123',
            first_name='Project',
            last_name='Manager'
        )

        self.client_obj = Client.objects.create(name='Test Client')

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user,
            billing_type='hourly',
            hourly_rate=Decimal('100.00')
        )

        # Add time entries
        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            duration_minutes=240  # 4 hours
        )

    def test_project_summary_serialization(self):
        """Test ProjectSummary serialization."""
        serializer = ProjectSummarySerializer(self.project)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Project')
        self.assertEqual(data['billing_type'], 'hourly')
        self.assertEqual(data['client_name'], 'Test Client')
        self.assertEqual(data['manager_name'], 'Project Manager')
        self.assertEqual(data['total_hours'], 4.0)
        self.assertEqual(data['team_size'], 0)


class ProjectTimelineSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )

        self.client_obj = Client.objects.create(name='Test Client')

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14)
        )

        # Create tasks with due dates
        Task.objects.create(
            project=self.project,
            title='Week 1 Task',
            due_date=date.today() + timedelta(days=3)
        )
        Task.objects.create(
            project=self.project,
            title='Week 2 Task',
            due_date=date.today() + timedelta(days=10)
        )

    def test_project_timeline_serialization(self):
        """Test ProjectTimeline serialization."""
        serializer = ProjectTimelineSerializer(self.project)
        data = serializer.data

        self.assertIn('project', data)
        self.assertIn('milestones', data)
        self.assertIn('tasks_by_week', data)
        self.assertIn('team_utilization', data)

        # Check project summary is included
        self.assertEqual(data['project']['name'], 'Test Project')

        # Check tasks are grouped by week
        tasks_by_week = data['tasks_by_week']
        self.assertGreater(len(tasks_by_week), 0)

        # Each week should have tasks
        total_tasks = sum(len(week['tasks']) for week in tasks_by_week)
        self.assertEqual(total_tasks, 2)


class ProjectMemberActionSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_member_action(self):
        """Test valid project member action."""
        data = {
            'user_id': str(self.user.id),
            'role': 'developer',
            'hourly_rate': '80.00',
            'allocation_percent': 75
        }

        serializer = ProjectMemberActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_user_id(self):
        """Test invalid user ID validation."""
        data = {
            'user_id': 'invalid-uuid',
            'role': 'developer'
        }

        serializer = ProjectMemberActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)

    def test_missing_user_id(self):
        """Test missing user ID validation."""
        data = {'role': 'developer'}

        serializer = ProjectMemberActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)


class ProjectStatsSerializerTest(TestCase):
    def test_project_stats_serialization(self):
        """Test ProjectStats serialization."""
        data = {
            'total_hours': '40.50',
            'billable_hours': '38.25',
            'total_cost': '3825.00',
            'budget_utilization': '85.50',
            'task_completion_rate': '72.30'
        }

        serializer = ProjectStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test the serialized data
        self.assertEqual(Decimal(serializer.validated_data['total_hours']), Decimal('40.50'))
        self.assertEqual(Decimal(serializer.validated_data['billable_hours']), Decimal('38.25'))
        self.assertEqual(Decimal(serializer.validated_data['total_cost']), Decimal('3825.00'))
        self.assertEqual(Decimal(serializer.validated_data['budget_utilization']), Decimal('85.50'))
        self.assertEqual(Decimal(serializer.validated_data['task_completion_rate']), Decimal('72.30'))

    def test_project_stats_methods(self):
        """Test ProjectStats serializer methods."""
        serializer = ProjectStatsSerializer()

        # Test hours_by_user method (returns empty list by default)
        self.assertEqual(serializer.get_hours_by_user(None), [])

        # Test hours_by_week method (returns empty list by default)
        self.assertEqual(serializer.get_hours_by_week(None), [])