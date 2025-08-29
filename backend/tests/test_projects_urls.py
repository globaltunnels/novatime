from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from projects.views import (
    ClientViewSet,
    ProjectViewSet,
    ProjectMemberViewSet,
    ProjectReportViewSet
)

User = get_user_model()


class ProjectsURLsTest(TestCase):
    """Test URL configuration for projects app."""

    def test_clients_list_url(self):
        """Test clients list URL resolves correctly."""
        url = reverse('projects:clients-list')
        self.assertEqual(url, '/api/v1/projects/clients/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ClientViewSet)
        self.assertEqual(resolver.url_name, 'clients-list')

    def test_clients_detail_url(self):
        """Test clients detail URL resolves correctly."""
        url = reverse('projects:clients-detail', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/clients/1/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ClientViewSet)
        self.assertEqual(resolver.url_name, 'clients-detail')
        self.assertEqual(resolver.kwargs, {'pk': '1'})

    def test_projects_list_url(self):
        """Test projects list URL resolves correctly."""
        url = reverse('projects:projects-list')
        self.assertEqual(url, '/api/v1/projects/projects/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-list')

    def test_projects_detail_url(self):
        """Test projects detail URL resolves correctly."""
        url = reverse('projects:projects-detail', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-detail')

    def test_projects_timeline_url(self):
        """Test projects timeline action URL resolves correctly."""
        url = reverse('projects:projects-timeline', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/timeline/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-timeline')

    def test_projects_stats_url(self):
        """Test projects stats action URL resolves correctly."""
        url = reverse('projects:projects-stats', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/stats/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-stats')

    def test_projects_add_member_url(self):
        """Test projects add member action URL resolves correctly."""
        url = reverse('projects:projects-add-member', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/add_member/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-add-member')

    def test_projects_remove_member_url(self):
        """Test projects remove member action URL resolves correctly."""
        url = reverse('projects:projects-remove-member', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/remove_member/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-remove-member')

    def test_projects_update_member_url(self):
        """Test projects update member action URL resolves correctly."""
        url = reverse('projects:projects-update-member', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/update_member/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-update-member')

    def test_projects_duplicate_url(self):
        """Test projects duplicate action URL resolves correctly."""
        url = reverse('projects:projects-duplicate', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/projects/1/duplicate/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-duplicate')

    def test_projects_dashboard_url(self):
        """Test projects dashboard action URL resolves correctly."""
        url = reverse('projects:projects-dashboard')
        self.assertEqual(url, '/api/v1/projects/projects/dashboard/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectViewSet)
        self.assertEqual(resolver.url_name, 'projects-dashboard')

    def test_project_members_list_url(self):
        """Test project members list URL resolves correctly."""
        url = reverse('projects:project-members-list')
        self.assertEqual(url, '/api/v1/projects/members/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectMemberViewSet)
        self.assertEqual(resolver.url_name, 'project-members-list')

    def test_project_members_detail_url(self):
        """Test project members detail URL resolves correctly."""
        url = reverse('projects:project-members-detail', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/v1/projects/members/1/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectMemberViewSet)
        self.assertEqual(resolver.url_name, 'project-members-detail')

    def test_project_reports_summary_url(self):
        """Test project reports summary action URL resolves correctly."""
        url = reverse('projects:project-reports-summary')
        self.assertEqual(url, '/api/v1/projects/reports/summary/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, ProjectReportViewSet)
        self.assertEqual(resolver.url_name, 'project-reports-summary')


class ProjectsURLAccessTest(APITestCase):
    """Test URL access and authentication for projects app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create organization and workspace for proper setup
        from organizations.models import Organization, Workspace, Membership
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access projects endpoints."""
        urls = [
            reverse('projects:clients-list'),
            reverse('projects:projects-list'),
            reverse('projects:project-members-list'),
            reverse('projects:project-reports-summary'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"URL {url} should require authentication"
            )

    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access projects endpoints."""
        self.client.force_authenticate(user=self.user)

        urls = [
            reverse('projects:clients-list'),
            reverse('projects:projects-list'),
            reverse('projects:project-members-list'),
        ]

        for url in urls:
            response = self.client.get(url)
            # Should return 200 OK or 404 if no data exists
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND],
                f"URL {url} should be accessible to authenticated users"
            )

    def test_project_reports_require_workspace(self):
        """Test that project reports require workspace parameter."""
        self.client.force_authenticate(user=self.user)

        url = reverse('projects:project-reports-summary')
        response = self.client.get(url)

        # Should return 400 Bad Request for missing workspace parameter
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProjectsURLPatternsTest(TestCase):
    """Test projects URL pattern configuration."""

    def test_no_duplicate_names(self):
        """Test that there are no duplicate URL names in projects."""
        from projects.urls import urlpatterns

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
            f"Found duplicate URL names in projects: {duplicates}"
        )

    def test_all_named_patterns_have_names(self):
        """Test that all patterns that should have names do have them."""
        from projects.urls import urlpatterns

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
        # Test that we can generate URLs for all expected endpoints
        expected_endpoints = [
            'projects:clients-list',
            'projects:clients-detail',
            'projects:projects-list',
            'projects:projects-detail',
            'projects:projects-timeline',
            'projects:projects-stats',
            'projects:projects-add-member',
            'projects:projects-remove-member',
            'projects:projects-update-member',
            'projects:projects-duplicate',
            'projects:projects-dashboard',
            'projects:project-members-list',
            'projects:project-members-detail',
            'projects:project-reports-summary',
        ]

        for endpoint in expected_endpoints:
            try:
                url = reverse(endpoint)
                self.assertTrue(url.startswith('/api/v1/projects/'))
            except Exception as e:
                self.fail(f"Failed to reverse URL for {endpoint}: {e}")

    def test_url_pattern_order(self):
        """Test that URL patterns are in the correct order."""
        from projects.urls import urlpatterns

        # Router patterns should come first
        router_patterns = [p for p in urlpatterns if hasattr(p, 'url_patterns')]

        # Should have one router include pattern
        self.assertEqual(len(router_patterns), 1)

        # The router should be the first pattern
        self.assertEqual(urlpatterns[0], router_patterns[0])

    def test_basename_consistency(self):
        """Test that router basenames are consistent."""
        from projects.urls import router

        # Check that registered basenames match expected patterns
        expected_basenames = {
            'clients': ClientViewSet,
            'projects': ProjectViewSet,
            'project-members': ProjectMemberViewSet,
            'project-reports': ProjectReportViewSet,
        }

        for basename, viewset_class in expected_basenames.items():
            # Check that the basename is registered
            registered = False
            for prefix, viewset, registered_basename in router.registry:
                if registered_basename == basename and viewset == viewset_class:
                    registered = True
                    break

            self.assertTrue(
                registered,
                f"ViewSet {viewset_class.__name__} not registered with basename '{basename}'"
            )

    def test_url_pattern_security(self):
        """Test that URL patterns don't expose sensitive information."""
        from projects.urls import urlpatterns

        # Check that no patterns contain sensitive information
        sensitive_patterns = ['password', 'secret', 'key', 'token']

        def check_pattern_security(patterns):
            for pattern in patterns:
                pattern_str = str(pattern.pattern)
                for sensitive in sensitive_patterns:
                    if sensitive in pattern_str.lower():
                        self.fail(f"URL pattern contains sensitive information: {pattern_str}")

        check_pattern_security(urlpatterns)

    def test_url_pattern_complexity(self):
        """Test that URL patterns are not overly complex."""
        from projects.urls import urlpatterns

        def check_pattern_complexity(patterns, depth=0):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include, check nested patterns
                    if depth > 2:  # Limit nesting depth
                        self.fail(f"URL pattern nesting too deep: {pattern}")
                    check_pattern_complexity(pattern.url_patterns, depth + 1)

        check_pattern_complexity(urlpatterns)