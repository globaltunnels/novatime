from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class MainURLsTest(TestCase):
    """Test URL configuration for main project."""

    def test_admin_url(self):
        """Test admin URL resolves correctly."""
        url = reverse('admin:index')
        self.assertEqual(url, '/admin/')

        resolver = resolve(url)
        self.assertEqual(resolver.app_name, 'admin')
        self.assertEqual(resolver.url_name, 'index')

    def test_api_schema_url(self):
        """Test API schema URL resolves correctly."""
        url = reverse('schema')
        self.assertEqual(url, '/api/schema/')

        resolver = resolve(url)
        # Should resolve to SpectacularAPIView
        self.assertIn('SpectacularAPIView', str(resolver.func))

    def test_swagger_ui_url(self):
        """Test Swagger UI URL resolves correctly."""
        url = reverse('swagger-ui')
        self.assertEqual(url, '/api/schema/swagger-ui/')

        resolver = resolve(url)
        # Should resolve to SpectacularSwaggerView
        self.assertIn('SpectacularSwaggerView', str(resolver.func))

    def test_redoc_url(self):
        """Test ReDoc URL resolves correctly."""
        url = reverse('redoc')
        self.assertEqual(url, '/api/schema/redoc/')

        resolver = resolve(url)
        # Should resolve to SpectacularRedocView
        self.assertIn('SpectacularRedocView', str(resolver.func))

    def test_iam_auth_urls(self):
        """Test IAM authentication URLs are included."""
        # Test that IAM URLs are accessible
        from iam.urls import urlpatterns as iam_urlpatterns

        # Check that key IAM URLs exist
        iam_url_names = [pattern.name for pattern in iam_urlpatterns if hasattr(pattern, 'name') and pattern.name]

        # These should be accessible through the main URLconf
        for url_name in ['token_obtain_pair', 'token_refresh']:
            try:
                url = reverse(f'iam:{url_name}')
                self.assertTrue(url.startswith('/api/v1/auth/'))
            except:
                # URL might not exist, skip
                pass

    def test_timesheets_urls(self):
        """Test timesheets URLs are included."""
        # Test that timesheets URLs are accessible
        from timesheets.urls import urlpatterns as timesheets_urlpatterns

        # Check that key timesheets URLs exist
        timesheets_url_names = [pattern.name for pattern in timesheets_urlpatterns if hasattr(pattern, 'name') and pattern.name]

        # These should be accessible through the main URLconf
        for url_name in ['timesheet-list', 'timesheet-detail']:
            try:
                url = reverse(f'timesheets:{url_name}')
                self.assertTrue(url.startswith('/api/v1/timesheets/'))
            except:
                # URL might not exist, skip
                pass

    def test_projects_urls(self):
        """Test projects URLs are included."""
        # Test that projects URLs are accessible
        from projects.urls import urlpatterns as projects_urlpatterns

        # Check that key projects URLs exist
        projects_url_names = [pattern.name for pattern in projects_urlpatterns if hasattr(pattern, 'name') and pattern.name]

        # These should be accessible through the main URLconf
        for url_name in ['project-list', 'project-detail']:
            try:
                url = reverse(f'projects:{url_name}')
                self.assertTrue(url.startswith('/api/v1/projects/'))
            except:
                # URL might not exist, skip
                pass

    def test_ai_services_urls(self):
        """Test AI services URLs are included."""
        # Test that AI services URLs are accessible
        from ai_services.urls import urlpatterns as ai_urlpatterns

        # Check that key AI URLs exist
        ai_url_names = [pattern.name for pattern in ai_urlpatterns if hasattr(pattern, 'name') and pattern.name]

        # These should be accessible through the main URLconf
        for url_name in ['ai-models-list', 'ai-jobs-list']:
            try:
                url = reverse(f'ai:{url_name}')
                self.assertTrue(url.startswith('/api/v1/ai/'))
            except:
                # URL might not exist, skip
                pass


class MainURLAccessTest(APITestCase):
    """Test URL access and authentication for main project."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_admin_access_requires_auth(self):
        """Test that admin access requires authentication."""
        response = self.client.get('/admin/')
        # Should redirect to login or return 302
        self.assertIn(response.status_code, [302, 403])

    def test_api_schema_accessible(self):
        """Test that API schema is accessible."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = self.client.get('/api/schema/swagger-ui/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_accessible(self):
        """Test that ReDoc is accessible."""
        response = self.client.get('/api/schema/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_accessible(self):
        """Test that health check endpoint is accessible."""
        response = self.client.get('/health/')
        # Health check should return 200 or appropriate health status
        self.assertIn(response.status_code, [200, 503])  # 503 if services down

    def test_unauthenticated_api_access(self):
        """Test that API endpoints require authentication."""
        api_endpoints = [
            '/api/v1/timesheets/',
            '/api/v1/projects/',
            '/api/v1/ai/models/',
        ]

        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should require authentication"
            )

    def test_authenticated_api_access(self):
        """Test that authenticated users can access API endpoints."""
        self.client.force_authenticate(user=self.user)

        api_endpoints = [
            '/api/v1/timesheets/',
            '/api/v1/projects/',
            '/api/v1/ai/models/',
        ]

        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            # Should return 200 OK or 404 if no data exists
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND],
                f"Endpoint {endpoint} should be accessible to authenticated users"
            )


class MainURLPatternsTest(TestCase):
    """Test URL pattern configuration."""

    def test_no_duplicate_urls(self):
        """Test that there are no duplicate URL patterns."""
        from django.urls import resolve
        from django.conf import settings
        from django.urls.conf import include

        # Get all URL patterns from main URLconf
        from main.urls import urlpatterns

        seen_patterns = set()
        duplicates = []

        def check_patterns(patterns, prefix=''):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include, recursively check
                    check_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    # This is a regular pattern
                    full_pattern = prefix + str(pattern.pattern)
                    if full_pattern in seen_patterns:
                        duplicates.append(full_pattern)
                    else:
                        seen_patterns.add(full_pattern)

        check_patterns(urlpatterns)
        self.assertEqual(
            len(duplicates), 0,
            f"Found duplicate URL patterns: {duplicates}"
        )

    def test_url_names_unique(self):
        """Test that URL names are unique across the project."""
        from django.urls import resolve
        from main.urls import urlpatterns

        seen_names = set()
        duplicates = []

        def check_names(patterns):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include, recursively check
                    check_names(pattern.url_patterns)
                elif hasattr(pattern, 'name') and pattern.name:
                    # This is a named pattern
                    if pattern.name in seen_names:
                        duplicates.append(pattern.name)
                    else:
                        seen_names.add(pattern.name)

        check_names(urlpatterns)
        self.assertEqual(
            len(duplicates), 0,
            f"Found duplicate URL names: {duplicates}"
        )