from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from iam.views import (
    CustomTokenObtainPairView,
    AuthViewSet,
    UserProfileView,
    ChangePasswordView
)
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


class IAMURLsTest(TestCase):
    """Test URL configuration for IAM app."""

    def test_token_obtain_url(self):
        """Test JWT token obtain URL resolves correctly."""
        url = reverse('iam:token_obtain_pair')
        self.assertEqual(url, '/api/v1/auth/token/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, CustomTokenObtainPairView)
        self.assertEqual(resolver.url_name, 'token_obtain_pair')

    def test_token_refresh_url(self):
        """Test JWT token refresh URL resolves correctly."""
        url = reverse('iam:token_refresh')
        self.assertEqual(url, '/api/v1/auth/token/refresh/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, TokenRefreshView)
        self.assertEqual(resolver.url_name, 'token_refresh')

    def test_user_profile_url(self):
        """Test user profile URL resolves correctly."""
        url = reverse('iam:user_profile')
        self.assertEqual(url, '/api/v1/auth/profile/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, UserProfileView)
        self.assertEqual(resolver.url_name, 'user_profile')

    def test_change_password_url(self):
        """Test change password URL resolves correctly."""
        url = reverse('iam:change_password')
        self.assertEqual(url, '/api/v1/auth/change-password/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, ChangePasswordView)
        self.assertEqual(resolver.url_name, 'change_password')

    def test_auth_register_url(self):
        """Test auth register URL resolves correctly."""
        url = reverse('iam:auth-register')
        self.assertEqual(url, '/api/v1/auth/register/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-register')

    def test_auth_verify_email_url(self):
        """Test auth verify email URL resolves correctly."""
        url = reverse('iam:auth-verify-email')
        self.assertEqual(url, '/api/v1/auth/verify_email/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-verify-email')

    def test_auth_request_password_reset_url(self):
        """Test auth request password reset URL resolves correctly."""
        url = reverse('iam:auth-request-password-reset')
        self.assertEqual(url, '/api/v1/auth/request_password_reset/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-request-password-reset')

    def test_auth_reset_password_url(self):
        """Test auth reset password URL resolves correctly."""
        url = reverse('iam:auth-reset-password')
        self.assertEqual(url, '/api/v1/auth/reset_password/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-reset-password')

    def test_auth_magic_link_url(self):
        """Test auth magic link URL resolves correctly."""
        url = reverse('iam:auth-magic-link')
        self.assertEqual(url, '/api/v1/auth/magic_link/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-magic-link')

    def test_auth_oidc_login_url(self):
        """Test auth OIDC login URL resolves correctly."""
        url = reverse('iam:auth-oidc-login')
        self.assertEqual(url, '/api/v1/auth/oidc_login/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-oidc-login')

    def test_auth_logout_url(self):
        """Test auth logout URL resolves correctly."""
        url = reverse('iam:auth-logout')
        self.assertEqual(url, '/api/v1/auth/logout/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-logout')

    def test_auth_list_url(self):
        """Test auth list URL resolves correctly."""
        url = reverse('iam:auth-list')
        self.assertEqual(url, '/api/v1/auth/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AuthViewSet)
        self.assertEqual(resolver.url_name, 'auth-list')


class IAMURLAccessTest(APITestCase):
    """Test URL access and authentication for IAM app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_token_endpoints_allow_any(self):
        """Test that token endpoints allow unauthenticated access."""
        token_urls = [
            reverse('iam:token_obtain_pair'),
            reverse('iam:token_refresh'),
        ]

        for url in token_urls:
            # These should return 401 for bad credentials, not 403
            response = self.client.post(url, {}, format='json')
            self.assertIn(
                response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]
            )

    def test_auth_allow_any_endpoints(self):
        """Test that auth endpoints allowing any access work."""
        allow_any_urls = [
            reverse('iam:auth-register'),
            reverse('iam:auth-verify-email'),
            reverse('iam:auth-request-password-reset'),
            reverse('iam:auth-reset-password'),
            reverse('iam:auth-magic-link'),
            reverse('iam:auth-oidc-login'),
        ]

        for url in allow_any_urls:
            response = self.client.post(url, {}, format='json')
            # Should return 400 for bad data, not 401/403
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication."""
        protected_urls = [
            reverse('iam:user_profile'),
            reverse('iam:change_password'),
            reverse('iam:auth-logout'),
        ]

        for url in protected_urls:
            response = self.client.get(url) if 'profile' in url else self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access protected endpoints."""
        self.client.force_authenticate(user=self.user)

        protected_urls = [
            (reverse('iam:user_profile'), 'get'),
            (reverse('iam:change_password'), 'post'),
            (reverse('iam:auth-logout'), 'post'),
        ]

        for url, method in protected_urls:
            if method == 'get':
                response = self.client.get(url)
            else:
                response = self.client.post(url)

            # Should return 200 OK or 400 for bad data
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
            )


class IAMURLPatternsTest(TestCase):
    """Test IAM URL pattern configuration."""

    def test_no_duplicate_names(self):
        """Test that there are no duplicate URL names in IAM."""
        from iam.urls import urlpatterns

        seen_names = set()
        duplicates = []

        def check_patterns(patterns):
            for pattern in patterns:
                if hasattr(pattern, 'name') and pattern.name:
                    if pattern.name in seen_names:
                        duplicates.append(pattern.name)
                    else:
                        seen_names.add(pattern.name)
                elif hasattr(pattern, 'url_patterns'):
                    # This is an include, recursively check
                    check_patterns(pattern.url_patterns)

        check_patterns(urlpatterns)
        self.assertEqual(
            len(duplicates), 0,
            f"Found duplicate URL names in IAM: {duplicates}"
        )

    def test_all_named_patterns_have_names(self):
        """Test that all patterns that should have names do have them."""
        from iam.urls import urlpatterns

        def check_named_patterns(patterns):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include, recursively check
                    check_named_patterns(pattern.url_patterns)
                elif hasattr(pattern, 'callback') and hasattr(pattern.callback, 'view_class'):
                    # This is a class-based view, should have a name
                    if not hasattr(pattern, 'name') or not pattern.name:
                        self.fail(f"Pattern {pattern.pattern} is missing a name")

        check_named_patterns(urlpatterns)

    def test_router_url_generation(self):
        """Test that router URLs can be generated correctly."""
        # Test that we can generate URLs for all expected auth endpoints
        expected_endpoints = [
            'iam:auth-list',
            'iam:auth-register',
            'iam:auth-verify-email',
            'iam:auth-request-password-reset',
            'iam:auth-reset-password',
            'iam:auth-magic-link',
            'iam:auth-oidc-login',
            'iam:auth-logout',
        ]

        for endpoint in expected_endpoints:
            try:
                url = reverse(endpoint)
                self.assertTrue(url.startswith('/api/v1/auth/'))
            except Exception as e:
                self.fail(f"Failed to reverse URL for {endpoint}: {e}")

    def test_url_pattern_order(self):
        """Test that URL patterns are in the correct order."""
        from iam.urls import urlpatterns

        # Token endpoints should come before router URLs
        token_patterns = [p for p in urlpatterns if 'token' in str(p.pattern)]
        router_patterns = [p for p in urlpatterns if hasattr(p, 'url_patterns')]

        # Token patterns should appear before router patterns
        token_indices = [urlpatterns.index(p) for p in token_patterns]
        router_indices = [urlpatterns.index(p) for p in router_patterns]

        if token_indices and router_indices:
            self.assertLess(
                max(token_indices), min(router_indices),
                "Token patterns should come before router patterns"
            )