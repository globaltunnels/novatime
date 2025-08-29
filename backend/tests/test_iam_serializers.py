import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from iam.models import Role
from iam.serializers import (
    UserRegistrationSerializer, CustomTokenObtainPairSerializer,
    UserProfileSerializer, PasswordChangeSerializer, RoleSerializer,
    EmailVerificationSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, MagicLinkRequestSerializer,
    OIDCTokenSerializer
)
import datetime

User = get_user_model()


class UserRegistrationSerializerTest(TestCase):
    def test_valid_user_registration(self):
        """Test successful user registration."""
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'phone_number': '+1234567890',
            'user_timezone': 'America/New_York'
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.phone_number, '+1234567890')
        self.assertEqual(user.user_timezone, 'America/New_York')
        self.assertTrue(user.check_password('StrongPass123!'))

    def test_password_mismatch_validation(self):
        """Test password mismatch validation."""
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass123!'
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_weak_password_validation(self):
        """Test weak password validation."""
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': '123',  # Too short
            'password_confirm': '123'
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class CustomTokenObtainPairSerializerTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_timezone='America/New_York'
        )

    def test_token_contains_custom_claims(self):
        """Test that JWT token contains custom user claims."""
        serializer = CustomTokenObtainPairSerializer()
        token = serializer.get_token(self.user)

        self.assertEqual(token['email'], 'test@example.com')
        self.assertEqual(token['first_name'], 'Test')
        self.assertEqual(token['last_name'], 'User')
        self.assertEqual(token['user_timezone'], 'America/New_York')


class UserProfileSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890',
            user_timezone='America/New_York',
            preferred_language='en',
            theme_preference='dark'
        )

    def test_user_profile_serialization(self):
        """Test user profile serialization."""
        serializer = UserProfileSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['phone_number'], '+1234567890')
        self.assertEqual(data['user_timezone'], 'America/New_York')
        self.assertEqual(data['preferred_language'], 'en')
        self.assertEqual(data['theme_preference'], 'dark')
        self.assertIn('date_joined', data)
        self.assertIn('last_login', data)

    def test_user_profile_update(self):
        """Test user profile update."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+0987654321',
            'preferred_language': 'es',
            'theme_preference': 'light'
        }

        serializer = UserProfileSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.phone_number, '+0987654321')
        self.assertEqual(updated_user.preferred_language, 'es')
        self.assertEqual(updated_user.theme_preference, 'light')


class PasswordChangeSerializerTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_valid_password_change(self):
        """Test successful password change."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        serializer = PasswordChangeSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())

    def test_incorrect_old_password(self):
        """Test incorrect old password validation."""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        serializer = PasswordChangeSerializer(data=data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_new_password_mismatch(self):
        """Test new password mismatch validation."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }

        serializer = PasswordChangeSerializer(data=data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class RoleSerializerTest(TestCase):
    def test_role_creation(self):
        """Test role creation."""
        data = {
            'name': 'Test Role',
            'description': 'A test role',
            'permissions': ['read', 'write'],
            'is_system_role': False
        }

        serializer = RoleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        role = serializer.save()

        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.description, 'A test role')
        self.assertEqual(role.permissions, ['read', 'write'])
        self.assertFalse(role.is_system_role)

    def test_role_serialization(self):
        """Test role serialization."""
        role = Role.objects.create(
            name='Admin Role',
            description='Administrator role',
            permissions=['read', 'write', 'delete'],
            is_system_role=True
        )

        serializer = RoleSerializer(role)
        data = serializer.data

        self.assertEqual(data['name'], 'Admin Role')
        self.assertEqual(data['description'], 'Administrator role')
        self.assertEqual(data['permissions'], ['read', 'write', 'delete'])
        self.assertTrue(data['is_system_role'])


class EmailVerificationSerializerTest(TestCase):
    def test_valid_token(self):
        """Test valid email verification token."""
        data = {'token': 'valid-jwt-token-here'}
        serializer = EmailVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_token(self):
        """Test missing token validation."""
        data = {}
        serializer = EmailVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)


class PasswordResetRequestSerializerTest(TestCase):
    def test_valid_email(self):
        """Test valid email for password reset request."""
        data = {'email': 'test@example.com'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_email(self):
        """Test invalid email validation."""
        data = {'email': 'invalid-email'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class PasswordResetConfirmSerializerTest(TestCase):
    def test_valid_password_reset(self):
        """Test valid password reset confirmation."""
        data = {
            'token': 'valid-reset-token',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test password mismatch in reset confirmation."""
        data = {
            'token': 'valid-reset-token',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class MagicLinkRequestSerializerTest(TestCase):
    def test_valid_email(self):
        """Test valid email for magic link request."""
        data = {'email': 'test@example.com'}
        serializer = MagicLinkRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_email(self):
        """Test invalid email validation."""
        data = {'email': 'invalid-email'}
        serializer = MagicLinkRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class OIDCTokenSerializerTest(TestCase):
    def test_valid_oidc_token(self):
        """Test valid OIDC token data."""
        data = {
            'provider': 'google',
            'access_token': 'valid-access-token'
        }

        serializer = OIDCTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_provider(self):
        """Test invalid provider validation."""
        data = {
            'provider': 'invalid_provider',
            'access_token': 'valid-access-token'
        }

        serializer = OIDCTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('provider', serializer.errors)

    def test_valid_providers(self):
        """Test all valid providers."""
        valid_providers = ['google', 'github', 'microsoft', 'apple']

        for provider in valid_providers:
            data = {
                'provider': provider,
                'access_token': 'valid-access-token'
            }

            serializer = OIDCTokenSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Provider {provider} should be valid")

    def test_missing_access_token(self):
        """Test missing access token validation."""
        data = {'provider': 'google'}
        serializer = OIDCTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('access_token', serializer.errors)