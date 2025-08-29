import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from iam.models import User

UserModel = get_user_model()


class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.date_joined)
        
    def test_superuser_creation(self):
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(admin_user.username, 'admin')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        
    def test_user_string_representation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(str(user), 'testuser')


class OrganizationModelTest(TestCase):
    def test_organization_creation(self):
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            description='A test organization'
        )
        
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.slug, 'test-org')
        self.assertEqual(org.description, 'A test organization')
        self.assertTrue(org.is_active)
        self.assertIsNotNone(org.created_at)
        
    def test_organization_string_representation(self):
        org = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        
        self.assertEqual(str(org), 'Test Organization')


class OrganizationMembershipModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        
    def test_organization_membership_creation(self):
        membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role='member'
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.organization, self.org)
        self.assertEqual(membership.role, 'member')
        self.assertTrue(membership.is_active)
        self.assertIsNotNone(membership.joined_at)
        
    def test_organization_membership_string_representation(self):
        membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role='admin'
        )
        
        expected_str = f"{self.user.username} in {self.org.name} ({membership.role})"
        self.assertEqual(str(membership), expected_str)