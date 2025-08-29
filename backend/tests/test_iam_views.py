import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core import mail
from unittest.mock import patch, MagicMock
from rest_framework_simplejwt.tokens import RefreshToken
from iam.models import Session, AuditLog
from organizations.models import Organization, Workspace
from organizations.models import Membership

User = get_user_model()


class CustomTokenObtainPairViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_successful_login(self):
        """Test successful JWT token obtain."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_wrong_credentials(self):
        """Test login with wrong credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_creates_session(self):
        """Test that successful login creates a session record."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check session was created
        self.assertTrue(Session.objects.filter(user=self.user).exists())
        session = Session.objects.filter(user=self.user).first()
        self.assertIsNotNone(session.session_key)
        self.assertIsNotNone(session.expires_at)

    def test_login_creates_audit_log(self):
        """Test that successful login creates audit log."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check audit log was created
        audit_log = AuditLog.objects.filter(
            user=self.user,
            action='login',
            resource_type='User'
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.details['method'], 'password')


class AuthViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_registration(self):
        """Test user registration."""
        url = reverse('iam:auth-register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')

        # Check audit log was created
        audit_log = AuditLog.objects.filter(
            user=user,
            action='register'
        ).first()
        self.assertIsNotNone(audit_log)

    def test_registration_with_existing_email(self):
        """Test registration with existing email fails."""
        url = reverse('iam:auth-register')
        data = {
            'email': 'test@example.com',  # Existing email
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('iam.views.send_mail')
    def test_email_verification(self, mock_send_mail):
        """Test email verification."""
        # First register a user
        url = reverse('iam:auth-register')
        data = {
            'email': 'verify@example.com',
            'username': 'verifyuser',
            'first_name': 'Verify',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }
        self.client.post(url, data, format='json')

        user = User.objects.get(email='verify@example.com')

        # Verify email
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        token = urlsafe_base64_encode(force_bytes(user.id))

        verify_url = reverse('iam:auth-verify-email')
        verify_data = {'token': token}

        response = self.client.post(verify_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    @patch('iam.views.send_mail')
    def test_request_password_reset(self, mock_send_mail):
        """Test password reset request."""
        url = reverse('iam:auth-request-password-reset')
        data = {'email': 'test@example.com'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check email was sent
        mock_send_mail.assert_called_once()

    @patch('iam.views.send_mail')
    def test_request_password_reset_nonexistent_email(self, mock_send_mail):
        """Test password reset request for nonexistent email."""
        url = reverse('iam:auth-request-password-reset')
        data = {'email': 'nonexistent@example.com'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Email should still be sent (to avoid revealing if email exists)
        mock_send_mail.assert_called_once()

    @patch('iam.views.send_mail')
    def test_password_reset_confirm(self, mock_send_mail):
        """Test password reset confirmation."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        # Request password reset first
        reset_url = reverse('iam:auth-request-password-reset')
        self.client.post(reset_url, {'email': 'test@example.com'}, format='json')

        # Generate reset token
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Confirm password reset
        confirm_url = reverse('iam:auth-reset-password')
        data = {
            'token': uid,
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        response = self.client.post(confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))

        # Check sessions were invalidated
        self.assertFalse(Session.objects.filter(user=self.user).exists())

    @patch('iam.views.send_mail')
    def test_magic_link_request(self, mock_send_mail):
        """Test magic link request."""
        url = reverse('iam:auth-magic-link')
        data = {'email': 'test@example.com'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check email was sent
        mock_send_mail.assert_called_once()

    @patch('iam.views.AuthViewSet.verify_oidc_token')
    def test_oidc_login_google(self, mock_verify_token):
        """Test OIDC login with Google."""
        mock_verify_token.return_value = {
            'email': 'google@example.com',
            'first_name': 'Google',
            'last_name': 'User',
            'sub': 'google123'
        }

        url = reverse('iam:auth-oidc-login')
        data = {
            'provider': 'google',
            'access_token': 'google_token_123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Check user was created
        user = User.objects.get(email='google@example.com')
        self.assertEqual(user.first_name, 'Google')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.provider, 'google')
        self.assertEqual(user.oidc_subject, 'google123')
        self.assertTrue(user.is_email_verified)

    @patch('iam.views.AuthViewSet.verify_oidc_token')
    def test_oidc_login_github(self, mock_verify_token):
        """Test OIDC login with GitHub."""
        mock_verify_token.return_value = {
            'email': 'github@example.com',
            'first_name': 'GitHub',
            'last_name': 'User',
            'sub': 'github123'
        }

        url = reverse('iam:auth-oidc-login')
        data = {
            'provider': 'github',
            'access_token': 'github_token_123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user was created
        user = User.objects.get(email='github@example.com')
        self.assertEqual(user.provider, 'github')

    def test_oidc_login_invalid_provider(self):
        """Test OIDC login with invalid provider."""
        url = reverse('iam:auth-oidc-login')
        data = {
            'provider': 'invalid_provider',
            'access_token': 'token_123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        """Test user logout."""
        # First login
        self.client.force_authenticate(user=self.user)

        # Create a session
        Session.objects.create(
            user=self.user,
            session_key='test_session',
            ip_address='127.0.0.1',
            user_agent='test-agent'
        )

        url = reverse('iam:auth-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check session was deleted
        self.assertFalse(Session.objects.filter(user=self.user).exists())

        # Check audit log was created
        audit_log = AuditLog.objects.filter(
            user=self.user,
            action='logout'
        ).first()
        self.assertIsNotNone(audit_log)


class UserProfileViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        """Test getting user profile."""
        url = reverse('iam:user-profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['phone_number'], '+1234567890')

    def test_update_user_profile(self):
        """Test updating user profile."""
        url = reverse('iam:user-profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+0987654321',
            'preferred_language': 'es'
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone_number, '+0987654321')
        self.assertEqual(self.user.preferred_language, 'es')

    def test_partial_update_user_profile(self):
        """Test partial update of user profile."""
        url = reverse('iam:user-profile')
        data = {'first_name': 'PartiallyUpdated'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check only specified field was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'PartiallyUpdated')
        self.assertEqual(self.user.last_name, 'User')  # Unchanged


class ChangePasswordViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        """Test successful password change."""
        url = reverse('iam:change-password')
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))

        # Check sessions were invalidated
        self.assertFalse(Session.objects.filter(user=self.user).exists())

        # Check audit log was created
        audit_log = AuditLog.objects.filter(
            user=self.user,
            action='password_change'
        ).first()
        self.assertIsNotNone(audit_log)

    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        url = reverse('iam:change-password')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords."""
        url = reverse('iam:change-password')
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)


class OIDCTokenVerificationTest(TestCase):
    """Test OIDC token verification."""

    def setUp(self):
        from iam.views import AuthViewSet
        self.viewset = AuthViewSet()

    @patch('iam.views.requests.get')
    def test_verify_google_token_success(self, mock_get):
        """Test successful Google token verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'email': 'google@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'id': 'google123'
        }
        mock_get.return_value = mock_response

        result = self.viewset.verify_oidc_token('google', 'test_token')
        self.assertIsNotNone(result)
        self.assertEqual(result['email'], 'google@example.com')
        self.assertEqual(result['first_name'], 'Google')
        self.assertEqual(result['last_name'], 'User')
        self.assertEqual(result['sub'], 'google123')

    @patch('iam.views.requests.get')
    def test_verify_github_token_success(self, mock_get):
        """Test successful GitHub token verification."""
        # Mock user info response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            'id': 123,
            'name': 'GitHub User',
            'email': 'github@example.com'
        }

        # Mock emails response
        emails_response = MagicMock()
        emails_response.status_code = 200
        emails_response.json.return_value = [
            {'email': 'github@example.com', 'primary': True}
        ]

        mock_get.side_effect = [user_response, emails_response]

        result = self.viewset.verify_oidc_token('github', 'test_token')
        self.assertIsNotNone(result)
        self.assertEqual(result['email'], 'github@example.com')
        self.assertEqual(result['first_name'], 'GitHub')
        self.assertEqual(result['last_name'], 'User')
        self.assertEqual(result['sub'], '123')

    @patch('iam.views.requests.get')
    def test_verify_token_failure(self, mock_get):
        """Test token verification failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        result = self.viewset.verify_oidc_token('google', 'invalid_token')
        self.assertIsNone(result)