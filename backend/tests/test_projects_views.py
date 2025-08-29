import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta
from projects.models import Client, Project, ProjectMember
from organizations.models import Organization, Workspace, Membership
from tasks.models import Task
from time_entries.models import TimeEntry

User = get_user_model()


class ClientViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@example.com',
            organization=self.organization
        )

        self.client.force_authenticate(user=self.user)

    def test_list_clients(self):
        """Test listing clients."""
        url = reverse('projects:client-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Client')

    def test_create_client(self):
        """Test creating a client."""
        url = reverse('projects:client-list')
        data = {
            'name': 'New Client',
            'email': 'newclient@example.com',
            'phone': '+1234567890',
            'default_hourly_rate': '150.00'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check client was created with correct organization
        client = Client.objects.get(name='New Client')
        self.assertEqual(client.organization, self.organization)

    def test_retrieve_client(self):
        """Test retrieving a specific client."""
        url = reverse('projects:client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Client')

    def test_update_client(self):
        """Test updating a client."""
        url = reverse('projects:client-detail', kwargs={'pk': self.client_obj.pk})
        data = {
            'name': 'Updated Client',
            'email': 'updated@example.com'
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check client was updated
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, 'Updated Client')

    def test_delete_client(self):
        """Test deleting a client."""
        url = reverse('projects:client-detail', kwargs={'pk': self.client_obj.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(pk=self.client_obj.pk).exists())


class ProjectViewSetTest(APITestCase):
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

        # Create membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            organization=self.organization
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user,
            billing_type='hourly',
            hourly_rate=Decimal('100.00'),
            budget_hours=100
        )

        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        """Test listing projects."""
        url = reverse('projects:project-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_project(self):
        """Test creating a project."""
        url = reverse('projects:project-list')
        data = {
            'name': 'New Project',
            'workspace': str(self.workspace.id),
            'client': str(self.client_obj.id),
            'manager': str(self.user.id),
            'billing_type': 'hourly',
            'hourly_rate': '120.00',
            'budget_hours': 80
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check project was created
        project = Project.objects.get(name='New Project')
        self.assertEqual(project.workspace, self.workspace)
        self.assertEqual(project.client, self.client_obj)

    def test_retrieve_project(self):
        """Test retrieving a specific project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')

    def test_update_project(self):
        """Test updating a project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.pk})
        data = {
            'name': 'Updated Project',
            'status': 'active'
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check project was updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')
        self.assertEqual(self.project.status, 'active')

    def test_delete_project(self):
        """Test deleting a project."""
        url = reverse('projects:project-detail', kwargs={'pk': self.project.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_workspace_filtering(self):
        """Test filtering projects by workspace."""
        url = reverse('projects:project-list')
        response = self.client.get(url, {'workspace': str(self.workspace.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_status_filtering(self):
        """Test filtering projects by status."""
        url = reverse('projects:project-list')
        response = self.client.get(url, {'status': 'planning'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_filtering(self):
        """Test searching projects."""
        url = reverse('projects:project-list')
        response = self.client.get(url, {'search': 'Test'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_project_timeline(self):
        """Test project timeline endpoint."""
        # Create some tasks
        Task.objects.create(
            project=self.project,
            title='Task 1',
            due_date=date.today() + timedelta(days=7)
        )

        url = reverse('projects:project-timeline', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('project', response.data)
        self.assertIn('tasks_by_week', response.data)

    def test_project_stats(self):
        """Test project stats endpoint."""
        # Create time entries
        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            duration_minutes=480,  # 8 hours
            is_billable=True
        )

        # Create tasks
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

        url = reverse('projects:project-stats', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_hours', response.data)
        self.assertIn('billable_hours', response.data)
        self.assertIn('total_cost', response.data)
        self.assertIn('task_completion_rate', response.data)

        # Check calculations
        self.assertEqual(Decimal(response.data['total_hours']), Decimal('8.00'))
        self.assertEqual(Decimal(response.data['billable_hours']), Decimal('8.00'))
        self.assertEqual(Decimal(response.data['total_cost']), Decimal('800.00'))  # 8 * 100
        self.assertEqual(Decimal(response.data['task_completion_rate']), Decimal('50.00'))  # 1/2 * 100

    def test_add_project_member(self):
        """Test adding a member to a project."""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )

        url = reverse('projects:project-add-member', kwargs={'pk': self.project.pk})
        data = {
            'user_id': str(new_user.id),
            'role': 'developer',
            'hourly_rate': '80.00',
            'allocation_percent': 75
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check member was added
        member = ProjectMember.objects.get(project=self.project, user=new_user)
        self.assertEqual(member.role, 'developer')
        self.assertEqual(member.hourly_rate, Decimal('80.00'))
        self.assertEqual(member.allocation_percent, 75)

    def test_add_existing_member_fails(self):
        """Test adding an existing member fails."""
        # Add user as member first
        ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='member'
        )

        url = reverse('projects:project-add-member', kwargs={'pk': self.project.pk})
        data = {'user_id': str(self.user.id)}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_project_member(self):
        """Test removing a member from a project."""
        # Add member first
        member = ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='member'
        )

        url = reverse('projects:project-remove-member', kwargs={'pk': self.project.pk})
        data = {'user_id': str(self.user.id)}

        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check member was removed
        self.assertFalse(ProjectMember.objects.filter(pk=member.pk).exists())

    def test_update_project_member(self):
        """Test updating a project member."""
        # Add member first
        ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='member',
            hourly_rate=Decimal('50.00'),
            allocation_percent=50
        )

        url = reverse('projects:project-update-member', kwargs={'pk': self.project.pk})
        data = {
            'user_id': str(self.user.id),
            'role': 'senior_developer',
            'hourly_rate': '90.00',
            'allocation_percent': 80
        }

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check member was updated
        member = ProjectMember.objects.get(project=self.project, user=self.user)
        self.assertEqual(member.role, 'senior_developer')
        self.assertEqual(member.hourly_rate, Decimal('90.00'))
        self.assertEqual(member.allocation_percent, 80)

    def test_duplicate_project(self):
        """Test duplicating a project."""
        # Add a member to the original project
        ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='developer'
        )

        # Create a task
        Task.objects.create(
            project=self.project,
            title='Original Task',
            status='in_progress'
        )

        url = reverse('projects:project-duplicate', kwargs={'pk': self.project.pk})
        data = {
            'copy_team': True,
            'copy_tasks': True
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check duplicate was created
        duplicate = Project.objects.get(name='Test Project (Copy)')
        self.assertEqual(duplicate.workspace, self.workspace)
        self.assertEqual(duplicate.status, 'planning')
        self.assertEqual(duplicate.manager, self.user)

        # Check team was copied
        self.assertEqual(duplicate.members.count(), 1)

        # Check tasks were copied (but reset to todo status)
        tasks = Task.objects.filter(project=duplicate)
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().status, 'todo')

    def test_project_dashboard(self):
        """Test project dashboard endpoint."""
        # Create another project
        project2 = Project.objects.create(
            name='Project 2',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user,
            status='active',
            end_date=date.today() - timedelta(days=1)  # Overdue
        )

        # Add user as member to both projects
        ProjectMember.objects.create(project=self.project, user=self.user)
        ProjectMember.objects.create(project=project2, user=self.user)

        url = reverse('projects:project-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('status_breakdown', response.data)
        self.assertIn('recent_projects', response.data)

        # Check summary calculations
        summary = response.data['summary']
        self.assertEqual(summary['total_projects'], 2)
        self.assertEqual(summary['active_projects'], 1)
        self.assertEqual(summary['overdue_projects'], 1)


class ProjectMemberViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            organization=self.organization
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj
        )

        self.member = ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='developer',
            hourly_rate=Decimal('75.00')
        )

        self.client.force_authenticate(user=self.user)

    def test_list_project_members(self):
        """Test listing project members."""
        url = reverse('projects:projectmember-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['role'], 'developer')

    def test_retrieve_project_member(self):
        """Test retrieving a specific project member."""
        url = reverse('projects:projectmember-detail', kwargs={'pk': self.member.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'developer')
        self.assertEqual(Decimal(response.data['hourly_rate']), Decimal('75.00'))


class ProjectReportViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            organization=self.organization
        )

        # Create multiple projects with different statuses and billing types
        self.project1 = Project.objects.create(
            name='Project 1',
            workspace=self.workspace,
            client=self.client_obj,
            status='active',
            billing_type='hourly',
            hourly_rate=Decimal('100.00'),
            budget_hours=100
        )

        self.project2 = Project.objects.create(
            name='Project 2',
            workspace=self.workspace,
            client=self.client_obj,
            status='completed',
            billing_type='fixed',
            fixed_price=Decimal('5000.00'),
            budget_hours=50
        )

        self.client.force_authenticate(user=self.user)

    def test_project_summary_report(self):
        """Test project summary report."""
        url = reverse('projects:projectreport-summary')
        response = self.client.get(url, {'workspace': str(self.workspace.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('status_distribution', response.data)
        self.assertIn('billing_distribution', response.data)

        # Check summary calculations
        summary = response.data['summary']
        self.assertEqual(summary['total_projects'], 2)
        self.assertEqual(Decimal(summary['total_budget_value']), Decimal('5000.00'))
        self.assertEqual(summary['total_budget_hours'], 150)

        # Check status distribution
        status_dist = response.data['status_distribution']
        self.assertEqual(status_dist['active'], 1)
        self.assertEqual(status_dist['completed'], 1)

        # Check billing distribution
        billing_dist = response.data['billing_distribution']
        self.assertEqual(billing_dist['hourly'], 1)
        self.assertEqual(billing_dist['fixed'], 1)

    def test_project_summary_report_missing_workspace(self):
        """Test project summary report with missing workspace parameter."""
        url = reverse('projects:projectreport-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_project_summary_report_with_date_filter(self):
        """Test project summary report with date filtering."""
        # Set dates on projects
        self.project1.start_date = date.today() - timedelta(days=10)
        self.project1.end_date = date.today() + timedelta(days=20)
        self.project1.save()

        self.project2.start_date = date.today() - timedelta(days=5)
        self.project2.end_date = date.today() + timedelta(days=15)
        self.project2.save()

        url = reverse('projects:projectreport-summary')
        params = {
            'workspace': str(self.workspace.id),
            'start_date': (date.today() - timedelta(days=7)).isoformat(),
            'end_date': (date.today() + timedelta(days=10)).isoformat()
        }

        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should include both projects
        summary = response.data['summary']
        self.assertEqual(summary['total_projects'], 2)

    def test_project_summary_report_invalid_date(self):
        """Test project summary report with invalid date format."""
        url = reverse('projects:projectreport-summary')
        params = {
            'workspace': str(self.workspace.id),
            'start_date': 'invalid-date',
            'end_date': '2023-12-31'
        }

        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)