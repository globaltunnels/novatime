import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Client, Project, ProjectMember

User = get_user_model()


class ClientModelTest(TestCase):
    def setUp(self):
        # Create organization first (required for Client)
        from organizations.models import Organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        
    def test_client_creation(self):
        client = Client.objects.create(
            organization=self.organization,
            name='Test Client',
            email='client@example.com',
            phone='+1234567890'
        )
        
        self.assertEqual(client.organization, self.organization)
        self.assertEqual(client.name, 'Test Client')
        self.assertEqual(client.email, 'client@example.com')
        self.assertEqual(client.phone, '+1234567890')
        self.assertTrue(client.is_active)
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)
        
    def test_client_string_representation(self):
        client = Client.objects.create(
            organization=self.organization,
            name='Test Client'
        )
        
        self.assertEqual(str(client), 'Test Client')


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for Project)
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
        
    def test_project_creation(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project',
            description='A test project for testing',
            status='active'
        )
        
        self.assertEqual(project.workspace, self.workspace)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.slug, 'test-project')
        self.assertEqual(project.description, 'A test project for testing')
        self.assertEqual(project.status, 'active')
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)
        
    def test_project_string_representation(self):
        project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project'
        )
        
        self.assertEqual(str(project), 'Test Project')


class ProjectMemberModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for Project)
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
        
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            slug='test-project'
        )
        
    def test_project_member_creation(self):
        member = ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='member'
        )
        
        self.assertEqual(member.project, self.project)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, 'member')
        self.assertTrue(member.is_active)
        self.assertIsNotNone(member.joined_at)
        
    def test_project_member_string_representation(self):
        member = ProjectMember.objects.create(
            project=self.project,
            user=self.user,
            role='manager'
        )
        
        expected_str = f"{self.user.username} in {self.project.name} ({member.role})"
        self.assertEqual(str(member), expected_str)