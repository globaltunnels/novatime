"""
Tests for accounts app.

This module contains comprehensive tests for the accounts app,
including model tests, serializer tests, and view tests.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.core.exceptions import ValidationError

from .models import (
    User, UserProfile, UserSession, PasswordResetToken,
    EmailVerificationToken, UserActivity
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserProfileSerializer, UserProfileCreateSerializer, UserSessionSerializer,
    PasswordResetTokenSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationTokenSerializer,
    EmailVerificationRequestSerializer, EmailVerificationConfirmSerializer,
    UserActivitySerializer, UserPreferencesSerializer, ChangePasswordSerializer,
    UserStatsSerializer, UserSearchSerializer, UserBulkActionSerializer,
    UserExportSerializer, UserImportSerializer, LoginSerializer,
    TokenRefreshSerializer, MagicLinkRequestSerializer, TwoFactorSetupSerializer,
    TwoFactorVerifySerializer, PasskeyRegisterSerializer,
    PasskeyAuthenticateSerializer, UserNotificationSerializer,
    UserSettingsSerializer, UserOnboardingSerializer, UserFeedbackSerializer
)

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test user creation."""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertEqual(self.user.get_short_name(), 'Test')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_verified)
        self.assertFalse(self.user.two_factor_enabled)
        self.assertFalse(self.user.passkeys_enabled)

    def test_user_str(self):
        """Test user string representation."""
        self.assertEqual(str(self.user), 'Test User')

    def test_user_save_sets_defaults(self):
        """Test that save sets default values."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.assertEqual(user.work_days, ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])

    def test_user_update_last_login(self):
        """Test updating last login."""
        old_login = self.user.last_login_at
        self.user.update_last_login()
        self.assertNotEqual(self.user.last_login_at, old_login)
        self.assertIsNotNone(self.user.last_login_at)

    def test_user_update_last_activity(self):
        """Test updating last activity."""
        old_activity = self.user.last_activity_at
        self.user.update_last_activity()
        self.assertNotEqual(self.user.last_activity_at, old_activity)
        self.assertIsNotNone(self.user.last_activity_at)

    def test_user_is_online(self):
        """Test user online status."""
        # User with recent activity should be online
        self.user.update_last_activity()
        self.assertTrue(self.user.is_online())

        # User with old activity should be offline
        self.user.last_activity_at = timezone.now() - timedelta(minutes=10)
        self.user.save()
        self.assertFalse(self.user.is_online())

        # User with no activity should be offline
        self.user.last_activity_at = None
        self.user.save()
        self.assertFalse(self.user.is_online())

    def test_user_get_profile_completion_percentage(self):
        """Test profile completion percentage."""
        # Empty profile should have low completion
        completion = self.user.get_profile_completion_percentage()
        self.assertGreaterEqual(completion, 0)
        self.assertLessEqual(completion, 100)

    def test_user_get_preferences(self):
        """Test getting user preferences."""
        preferences = self.user.get_preferences()
        self.assertIn('timezone', preferences)
        self.assertIn('language', preferences)
        self.assertIn('work_hours_start', preferences)
        self.assertIn('work_hours_end', preferences)
        self.assertIn('work_days', preferences)

    def test_user_update_preferences(self):
        """Test updating user preferences."""
        new_preferences = {
            'timezone': 'America/New_York',
            'language': 'en',
            'email_notifications': False
        }
        self.user.update_preferences(new_preferences)

        self.assertEqual(self.user.timezone, 'America/New_York')
        self.assertEqual(self.user.language, 'en')
        self.assertFalse(self.user.email_notifications)

    def test_user_enable_disable_two_factor(self):
        """Test enabling and disabling two-factor authentication."""
        # Enable
        self.user.enable_two_factor()
        self.assertTrue(self.user.two_factor_enabled)

        # Disable
        self.user.disable_two_factor()
        self.assertFalse(self.user.two_factor_enabled)


class UserProfileModelTest(TestCase):
    """Test UserProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            location='New York, NY',
            years_of_experience=5,
            linkedin_url='https://linkedin.com/in/testuser'
        )

    def test_profile_creation(self):
        """Test profile creation."""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.location, 'New York, NY')
        self.assertEqual(self.profile.years_of_experience, 5)
        self.assertEqual(self.profile.linkedin_url, 'https://linkedin.com/in/testuser')
        self.assertEqual(self.profile.theme, 'system')

    def test_profile_str(self):
        """Test profile string representation."""
        expected = "Profile for Test User"
        self.assertEqual(str(self.profile), expected)

    def test_profile_get_completion_percentage(self):
        """Test profile completion percentage."""
        completion = self.profile.get_completion_percentage()
        self.assertGreaterEqual(completion, 0)
        self.assertLessEqual(completion, 100)

        # Add more fields to increase completion
        self.profile.date_of_birth = timezone.now().date()
        self.profile.bio = 'Test bio'
        self.profile.save()

        new_completion = self.profile.get_completion_percentage()
        self.assertGreaterEqual(new_completion, completion)


class UserSessionModelTest(TestCase):
    """Test UserSession model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.session = UserSession.objects.create(
            user=self.user,
            session_key='test-session-key',
            device_type='desktop',
            device_name='Chrome on Windows',
            ip_address='192.168.1.1',
            expires_at=timezone.now() + timedelta(hours=24)
        )

    def test_session_creation(self):
        """Test session creation."""
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.session_key, 'test-session-key')
        self.assertEqual(self.session.device_type, 'desktop')
        self.assertEqual(self.session.device_name, 'Chrome on Windows')
        self.assertEqual(self.session.ip_address, '192.168.1.1')
        self.assertTrue(self.session.is_active)
        self.assertIsNotNone(self.session.created_at)
        self.assertIsNotNone(self.session.last_activity_at)
        self.assertIsNotNone(self.session.expires_at)

    def test_session_str(self):
        """Test session string representation."""
        expected = "Session for Test User (desktop)"
        self.assertEqual(str(self.session), expected)

    def test_session_is_expired(self):
        """Test session expiration check."""
        # Not expired
        self.assertFalse(self.session.is_expired())

        # Expired
        self.session.expires_at = timezone.now() - timedelta(seconds=1)
        self.session.save()
        self.assertTrue(self.session.is_expired())

    def test_session_extend(self):
        """Test session extension."""
        old_expires_at = self.session.expires_at
        self.session.extend(hours=48)

        self.assertGreater(self.session.expires_at, old_expires_at)
        self.assertFalse(self.session.is_expired())

    def test_session_update_activity(self):
        """Test updating session activity."""
        old_activity = self.session.last_activity_at
        self.session.update_activity()

        self.assertGreater(self.session.last_activity_at, old_activity)


class PasswordResetTokenModelTest(TestCase):
    """Test PasswordResetToken model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24)
        )

    def test_token_creation(self):
        """Test token creation."""
        self.assertEqual(self.token.user, self.user)
        self.assertIsNotNone(self.token.token)
        self.assertFalse(self.token.is_used)
        self.assertIsNotNone(self.token.created_at)
        self.assertIsNotNone(self.token.expires_at)

    def test_token_str(self):
        """Test token string representation."""
        expected = "Password reset for Test User"
        self.assertEqual(str(self.token), expected)

    def test_token_is_expired(self):
        """Test token expiration check."""
        # Not expired
        self.assertFalse(self.token.is_expired())

        # Expired
        self.token.expires_at = timezone.now() - timedelta(seconds=1)
        self.token.save()
        self.assertTrue(self.token.is_expired())

    def test_token_use(self):
        """Test token usage."""
        # Use token
        result = self.token.use()
        self.assertTrue(result)
        self.assertTrue(self.token.is_used)
        self.assertIsNotNone(self.token.used_at)

        # Try to use again
        result = self.token.use()
        self.assertFalse(result)


class EmailVerificationTokenModelTest(TestCase):
    """Test EmailVerificationToken model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = EmailVerificationToken.objects.create(
            user=self.user,
            email='test@example.com',
            expires_at=timezone.now() + timedelta(days=7)
        )

    def test_token_creation(self):
        """Test token creation."""
        self.assertEqual(self.token.user, self.user)
        self.assertEqual(self.token.email, 'test@example.com')
        self.assertIsNotNone(self.token.token)
        self.assertFalse(self.token.is_verified)
        self.assertIsNotNone(self.token.created_at)
        self.assertIsNotNone(self.token.expires_at)

    def test_token_str(self):
        """Test token string representation."""
        expected = "Email verification for test@example.com"
        self.assertEqual(str(self.token), expected)

    def test_token_is_expired(self):
        """Test token expiration check."""
        # Not expired
        self.assertFalse(self.token.is_expired())

        # Expired
        self.token.expires_at = timezone.now() - timedelta(seconds=1)
        self.token.save()
        self.assertTrue(self.token.is_expired())

    def test_token_verify(self):
        """Test token verification."""
        # Verify token
        result = self.token.verify()
        self.assertTrue(result)
        self.assertTrue(self.token.is_verified)
        self.assertIsNotNone(self.token.verified_at)
        self.assertTrue(self.token.user.is_verified)

        # Try to verify again
        result = self.token.verify()
        self.assertFalse(result)


class UserActivityModelTest(TestCase):
    """Test UserActivity model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.activity = UserActivity.objects.create(
            user=self.user,
            action='user_logged_in',
            description='User logged in',
            category='auth',
            ip_address='192.168.1.1'
        )

    def test_activity_creation(self):
        """Test activity creation."""
        self.assertEqual(self.activity.user, self.user)
        self.assertEqual(self.activity.action, 'user_logged_in')
        self.assertEqual(self.activity.description, 'User logged in')
        self.assertEqual(self.activity.category, 'auth')
        self.assertEqual(self.activity.ip_address, '192.168.1.1')
        self.assertIsNotNone(self.activity.created_at)

    def test_activity_str(self):
        """Test activity string representation."""
        expected = "Test User: user_logged_in ("
        self.assertTrue(str(self.activity).startswith(expected))


# Pytest-style tests
@pytest.mark.django_db
def test_user_serializer():
    """Test UserSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        first_name='Test',
        last_name='User',
        password='testpass123'
    )

    serializer = UserSerializer(user)
    data = serializer.data

    assert data['email'] == 'test@example.com'
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'User'
    assert data['full_name'] == 'Test User'
    assert data['is_active'] is True
    assert data['is_verified'] is False
    assert 'profile_completion' in data
    assert 'organizations_count' in data


@pytest.mark.django_db
def test_user_create_serializer():
    """Test UserCreateSerializer."""
    data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }

    serializer = UserCreateSerializer(data=data)
    assert serializer.is_valid()

    user = serializer.save()
    assert user.email == 'test@example.com'
    assert user.first_name == 'Test'
    assert user.check_password('testpass123')


@pytest.mark.django_db
def test_user_profile_serializer():
    """Test UserProfileSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    profile = UserProfile.objects.create(
        user=user,
        location='New York, NY',
        years_of_experience=5
    )

    serializer = UserProfileSerializer(profile)
    data = serializer.data

    assert data['user'] == user.id
    assert data['location'] == 'New York, NY'
    assert data['years_of_experience'] == 5
    assert 'completion_percentage' in data


@pytest.mark.django_db
def test_user_session_serializer():
    """Test UserSessionSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    session = UserSession.objects.create(
        user=user,
        session_key='test-key',
        device_type='desktop',
        expires_at=timezone.now() + timedelta(hours=24)
    )

    serializer = UserSessionSerializer(session)
    data = serializer.data

    assert data['user'] == user.id
    assert data['session_key'] == 'test-key'
    assert data['device_type'] == 'desktop'
    assert data['is_active'] is True
    assert data['is_expired'] is False


@pytest.mark.django_db
def test_password_reset_token_serializer():
    """Test PasswordResetTokenSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24)
    )

    serializer = PasswordResetTokenSerializer(token)
    data = serializer.data

    assert data['user'] == user.id
    assert data['is_used'] is False
    assert data['is_expired'] is False


@pytest.mark.django_db
def test_email_verification_token_serializer():
    """Test EmailVerificationTokenSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    token = EmailVerificationToken.objects.create(
        user=user,
        email='test@example.com',
        expires_at=timezone.now() + timedelta(days=7)
    )

    serializer = EmailVerificationTokenSerializer(token)
    data = serializer.data

    assert data['user'] == user.id
    assert data['email'] == 'test@example.com'
    assert data['is_verified'] is False
    assert data['is_expired'] is False


@pytest.mark.django_db
def test_user_activity_serializer():
    """Test UserActivitySerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    activity = UserActivity.objects.create(
        user=user,
        action='user_logged_in',
        description='User logged in',
        category='auth'
    )

    serializer = UserActivitySerializer(activity)
    data = serializer.data

    assert data['user'] == user.id
    assert data['action'] == 'user_logged_in'
    assert data['description'] == 'User logged in'
    assert data['category'] == 'auth'


@pytest.mark.django_db
def test_user_workflow():
    """Test complete user workflow."""
    # Create user
    user = User.objects.create_user(
        email='test@example.com',
        first_name='Test',
        last_name='User',
        password='testpass123'
    )

    assert user.email == 'test@example.com'
    assert user.get_full_name() == 'Test User'
    assert user.is_active is True
    assert user.is_verified is False

    # Create profile
    profile = UserProfile.objects.create(
        user=user,
        location='New York, NY'
    )

    assert profile.user == user
    assert profile.location == 'New York, NY'

    # Create session
    session = UserSession.objects.create(
        user=user,
        session_key='test-session',
        device_type='desktop',
        expires_at=timezone.now() + timedelta(hours=24)
    )

    assert session.user == user
    assert session.is_active is True
    assert not session.is_expired()

    # Create password reset token
    reset_token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24)
    )

    assert reset_token.user == user
    assert not reset_token.is_used
    assert not reset_token.is_expired()

    # Create email verification token
    verification_token = EmailVerificationToken.objects.create(
        user=user,
        email='test@example.com',
        expires_at=timezone.now() + timedelta(days=7)
    )

    assert verification_token.user == user
    assert verification_token.email == 'test@example.com'
    assert not verification_token.is_verified
    assert not verification_token.is_expired()

    # Create activity
    activity = UserActivity.objects.create(
        user=user,
        action='user_registered',
        description='User registered',
        category='auth'
    )

    assert activity.user == user
    assert activity.action == 'user_registered'
    assert activity.category == 'auth'


@pytest.mark.django_db
def test_user_preferences_workflow():
    """Test user preferences workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Get initial preferences
    preferences = user.get_preferences()
    assert 'timezone' in preferences
    assert 'language' in preferences

    # Update preferences
    new_preferences = {
        'timezone': 'America/New_York',
        'language': 'en',
        'email_notifications': False
    }
    user.update_preferences(new_preferences)

    # Check updated preferences
    updated_preferences = user.get_preferences()
    assert updated_preferences['timezone'] == 'America/New_York'
    assert updated_preferences['language'] == 'en'
    assert updated_preferences['email_notifications'] is False


@pytest.mark.django_db
def test_two_factor_workflow():
    """Test two-factor authentication workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Initially disabled
    assert not user.two_factor_enabled

    # Enable
    user.enable_two_factor()
    assert user.two_factor_enabled

    # Disable
    user.disable_two_factor()
    assert not user.two_factor_enabled


@pytest.mark.django_db
def test_session_workflow():
    """Test session workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Create session
    session = UserSession.objects.create(
        user=user,
        session_key='test-session',
        device_type='desktop',
        expires_at=timezone.now() + timedelta(hours=24)
    )

    assert session.is_active
    assert not session.is_expired()

    # Update activity
    old_activity = session.last_activity_at
    session.update_activity()
    assert session.last_activity_at > old_activity

    # Extend session
    old_expires = session.expires_at
    session.extend(hours=48)
    assert session.expires_at > old_expires


@pytest.mark.django_db
def test_token_workflow():
    """Test token workflow."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Password reset token
    reset_token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=24)
    )

    assert not reset_token.is_used
    assert not reset_token.is_expired()

    # Use token
    result = reset_token.use()
    assert result
    assert reset_token.is_used
    assert reset_token.used_at is not None

    # Email verification token
    verification_token = EmailVerificationToken.objects.create(
        user=user,
        email='test@example.com',
        expires_at=timezone.now() + timedelta(days=7)
    )

    assert not verification_token.is_verified
    assert not verification_token.is_expired()

    # Verify token
    result = verification_token.verify()
    assert result
    assert verification_token.is_verified
    assert verification_token.verified_at is not None
    assert user.is_verified


@pytest.mark.django_db
def test_activity_logging():
    """Test activity logging."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Create activities
    activity1 = UserActivity.objects.create(
        user=user,
        action='user_logged_in',
        description='User logged in',
        category='auth'
    )

    activity2 = UserActivity.objects.create(
        user=user,
        action='profile_updated',
        description='Profile updated',
        category='profile'
    )

    # Check activities
    activities = UserActivity.objects.filter(user=user)
    assert activities.count() == 2

    # Check ordering
    assert activities.first() == activity2  # Most recent first
    assert activities.last() == activity1   # Oldest last


@pytest.mark.django_db
def test_user_search():
    """Test user search functionality."""
    # Create test users
    user1 = User.objects.create_user(
        email='john@example.com',
        first_name='John',
        last_name='Doe',
        password='testpass123'
    )

    user2 = User.objects.create_user(
        email='jane@example.com',
        first_name='Jane',
        last_name='Smith',
        password='testpass123'
    )

    user3 = User.objects.create_user(
        email='bob@example.com',
        first_name='Bob',
        last_name='Johnson',
        password='testpass123'
    )

    # Search by email
    users = User.objects.filter(
        Q(email__icontains='john') |
        Q(first_name__icontains='john') |
        Q(last_name__icontains='john')
    )
    assert users.count() == 2  # john@example.com and bob@example.com

    # Search by name
    users = User.objects.filter(
        Q(first_name__icontains='Jane') |
        Q(last_name__icontains='Jane')
    )
    assert users.count() == 1
    assert users.first() == user2


@pytest.mark.django_db
def test_user_bulk_operations():
    """Test bulk user operations."""
    # Create test users
    users = []
    for i in range(5):
        user = User.objects.create_user(
            email=f'user{i}@example.com',
            password='testpass123'
        )
        users.append(user)

    # Bulk activate
    User.objects.filter(id__in=[u.id for u in users]).update(is_active=True)
    active_count = User.objects.filter(is_active=True).count()
    assert active_count >= 5

    # Bulk deactivate
    User.objects.filter(id__in=[u.id for u in users]).update(is_active=False)
    inactive_count = User.objects.filter(is_active=False).count()
    assert inactive_count >= 5


@pytest.mark.django_db
def test_user_stats():
    """Test user statistics."""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # Create sessions
    for i in range(3):
        UserSession.objects.create(
            user=user,
            session_key=f'session-{i}',
            device_type='desktop' if i % 2 == 0 else 'mobile',
            expires_at=timezone.now() + timedelta(hours=24)
        )

    # Create activities
    for i in range(5):
        UserActivity.objects.create(
            user=user,
            action=f'action_{i}',
            description=f'Description {i}',
            category='auth' if i % 2 == 0 else 'profile'
        )

    # Check counts
    session_count = UserSession.objects.filter(user=user).count()
    activity_count = UserActivity.objects.filter(user=user).count()

    assert session_count == 3
    assert activity_count == 5


@pytest.mark.django_db
def test_user_preferences_serializer():
    """Test UserPreferencesSerializer."""
    data = {
        'timezone': 'America/New_York',
        'language': 'en',
        'work_hours_start': '09:00:00',
        'work_hours_end': '17:00:00',
        'work_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'email_notifications': True,
        'push_notifications': False,
        'weekly_digest': True,
        'profile_visibility': 'team',
        'show_online_status': True
    }

    serializer = UserPreferencesSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['timezone'] == 'America/New_York'
    assert validated_data['language'] == 'en'
    assert validated_data['email_notifications'] is True


@pytest.mark.django_db
def test_change_password_serializer():
    """Test ChangePasswordSerializer."""
    user = User.objects.create_user(
        email='test@example.com',
        password='oldpassword123'
    )

    data = {
        'current_password': 'oldpassword123',
        'new_password': 'newpassword123',
        'new_password_confirm': 'newpassword123'
    }

    serializer = ChangePasswordSerializer(data=data)
    serializer.context['request'] = type('Request', (), {'user': user})()

    assert serializer.is_valid()

    # Change password
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    assert user.check_password('newpassword123')


@pytest.mark.django_db
def test_login_serializer():
    """Test LoginSerializer."""
    User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    data = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'remember_me': True
    }

    serializer = LoginSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['email'] == 'test@example.com'
    assert validated_data['password'] == 'testpass123'
    assert validated_data['remember_me'] is True


@pytest.mark.django_db
def test_user_feedback_serializer():
    """Test UserFeedbackSerializer."""
    data = {
        'type': 'feature',
        'subject': 'New feature request',
        'message': 'Please add dark mode support',
        'category': 'ui',
        'priority': 'medium'
    }

    serializer = UserFeedbackSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['type'] == 'feature'
    assert validated_data['subject'] == 'New feature request'
    assert validated_data['priority'] == 'medium'


@pytest.mark.django_db
def test_user_onboarding_serializer():
    """Test UserOnboardingSerializer."""
    data = {
        'step': 3,
        'completed_steps': [1, 2],
        'data': {
            'timezone': 'America/New_York',
            'work_hours_start': '09:00:00'
        }
    }

    serializer = UserOnboardingSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['step'] == 3
    assert validated_data['completed_steps'] == [1, 2]
    assert validated_data['data']['timezone'] == 'America/New_York'


@pytest.mark.django_db
def test_user_settings_serializer():
    """Test UserSettingsSerializer."""
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'timezone': 'America/New_York',
        'language': 'en',
        'work_hours_start': '09:00:00',
        'work_hours_end': '17:00:00',
        'work_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'email_notifications': True,
        'push_notifications': False,
        'weekly_digest': True,
        'profile_visibility': 'team',
        'show_online_status': True
    }

    serializer = UserSettingsSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['first_name'] == 'John'
    assert validated_data['timezone'] == 'America/New_York'
    assert validated_data['email_notifications'] is True


@pytest.mark.django_db
def test_user_search_serializer():
    """Test UserSearchSerializer."""
    data = {
        'query': 'john',
        'organization_id': '123e4567-e89b-12d3-a456-426614174000',
        'workspace_id': '123e4567-e89b-12d3-a456-426614174001',
        'limit': 10
    }

    serializer = UserSearchSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['query'] == 'john'
    assert validated_data['limit'] == 10


@pytest.mark.django_db
def test_user_bulk_action_serializer():
    """Test UserBulkActionSerializer."""
    data = {
        'user_ids': [
            '123e4567-e89b-12d3-a456-426614174000',
            '123e4567-e89b-12d3-a456-426614174001'
        ],
        'action': 'activate'
    }

    serializer = UserBulkActionSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert len(validated_data['user_ids']) == 2
    assert validated_data['action'] == 'activate'


@pytest.mark.django_db
def test_user_export_serializer():
    """Test UserExportSerializer."""
    data = {
        'include_profile': True,
        'include_sessions': False,
        'include_activities': True,
        'include_organizations': True,
        'include_workspaces': True,
        'include_teams': True,
        'include_tasks': False,
        'include_time_entries': False,
        'date_from': '2024-01-01',
        'date_to': '2024-12-31',
        'format': 'json'
    }

    serializer = UserExportSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['include_profile'] is True
    assert validated_data['format'] == 'json'


@pytest.mark.django_db
def test_user_import_serializer():
    """Test UserImportSerializer."""
    # Mock file upload
    from django.core.files.uploadedfile import SimpleUploadedFile
    file_content = b'{"users": []}'
    uploaded_file = SimpleUploadedFile(
        'users.json',
        file_content,
        content_type='application/json'
    )

    data = {
        'file': uploaded_file,
        'import_mode': 'create',
        'send_invitation': True
    }

    serializer = UserImportSerializer(data=data)
    assert serializer.is_valid()

    validated_data = serializer.validated_data
    assert validated_data['import_mode'] == 'create'
    assert validated_data['send_invitation'] is True