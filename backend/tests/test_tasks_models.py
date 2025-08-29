import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from tasks.models import TaskLabel, Task

User = get_user_model()


class TaskLabelModelTest(TestCase):
    def setUp(self):
        # Create organization and workspace first (required for TaskLabel)
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
        
    def test_task_label_creation(self):
        label = TaskLabel.objects.create(
            workspace=self.workspace,
            name='Test Label',
            color='#FF0000',
            description='A test label for testing'
        )
        
        self.assertEqual(label.workspace, self.workspace)
        self.assertEqual(label.name, 'Test Label')
        self.assertEqual(label.color, '#FF0000')
        self.assertEqual(label.description, 'A test label for testing')
        self.assertIsNotNone(label.created_at)
        
    def test_task_label_string_representation(self):
        label = TaskLabel.objects.create(
            workspace=self.workspace,
            name='Test Label'
        )
        
        self.assertEqual(str(label), 'Test Label')


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace first (required for Task)
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
        
        self.project = None  # Project is optional for Task
        
    def test_task_creation(self):
        task = Task.objects.create(
            workspace=self.workspace,
            title='Test Task',
            description='A test task for testing',
            assigned_to=self.user,
            status='todo',
            priority='medium'
        )
        
        self.assertEqual(task.workspace, self.workspace)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'A test task for testing')
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.status, 'todo')
        self.assertEqual(task.priority, 'medium')
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        
    def test_task_string_representation(self):
        task = Task.objects.create(
            workspace=self.workspace,
            title='Test Task'
        )
        
        self.assertEqual(str(task), 'Test Task')