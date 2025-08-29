import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from organizations.models import Organization, Workspace, Membership

User = get_user_model()


class OrganizationModelTest(TestCase):
    def test_organization_creation(self):
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            description='A test organization for testing'
        )
        
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.slug, 'test-org')
        self.assertEqual(org.description, 'A test organization for testing')
        self.assertTrue(org.is_active)
        self.assertIsNotNone(org.created_at)
        
    def test_organization_string_representation(self):
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        
        self.assertEqual(str(org), 'Test Organization')


class WorkspaceModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        
    def test_workspace_creation(self):
        workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace',
            description='A test workspace'
        )
        
        self.assertEqual(workspace.organization, self.organization)
        self.assertEqual(workspace.name, 'Test Workspace')
        self.assertEqual(workspace.description, 'A test workspace')
        self.assertFalse(workspace.is_private)
        self.assertIsNotNone(workspace.created_at)
        self.assertIsNotNone(workspace.updated_at)
        
    def test_workspace_string_representation(self):
        workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )
        
        self.assertEqual(str(workspace), 'Test Organization - Test Workspace')


class MembershipModelTest(TestCase):
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
        
    def test_membership_creation(self):
        membership = Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member',
            is_active=True
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.workspace, self.workspace)
        self.assertEqual(membership.role, 'member')
        self.assertTrue(membership.is_active)
        self.assertIsNotNone(membership.joined_at)
        self.assertIsNotNone(membership.updated_at)
        
    def test_membership_string_representation(self):
        membership = Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='admin'
        )
        
        expected_str = f"{self.user.email} - {self.workspace.name} ({membership.role})"
        self.assertEqual(str(membership), expected_str)