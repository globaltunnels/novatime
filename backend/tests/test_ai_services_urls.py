from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from ai_services.views import (
    AIModelViewSet,
    AIJobViewSet,
    SmartTimesheetSuggestionViewSet,
    TaskAssignmentRecommendationViewSet,
    AIInsightViewSet
)

User = get_user_model()


class AIServicesURLsTest(TestCase):
    """Test URL configuration for ai_services app."""

    def test_ai_models_list_url(self):
        """Test AI models list URL resolves correctly."""
        url = reverse('ai-models-list')
        self.assertEqual(url, '/api/ai/models/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIModelViewSet)
        self.assertEqual(resolver.url_name, 'ai-models-list')

    def test_ai_models_detail_url(self):
        """Test AI models detail URL resolves correctly."""
        url = reverse('ai-models-detail', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/models/1/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIModelViewSet)
        self.assertEqual(resolver.url_name, 'ai-models-detail')
        self.assertEqual(resolver.kwargs, {'pk': '1'})

    def test_ai_jobs_list_url(self):
        """Test AI jobs list URL resolves correctly."""
        url = reverse('ai-jobs-list')
        self.assertEqual(url, '/api/ai/jobs/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIJobViewSet)
        self.assertEqual(resolver.url_name, 'ai-jobs-list')

    def test_ai_jobs_detail_url(self):
        """Test AI jobs detail URL resolves correctly."""
        url = reverse('ai-jobs-detail', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/jobs/1/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIJobViewSet)
        self.assertEqual(resolver.url_name, 'ai-jobs-detail')

    def test_ai_jobs_cancel_url(self):
        """Test AI jobs cancel action URL resolves correctly."""
        url = reverse('ai-jobs-cancel', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/jobs/1/cancel/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIJobViewSet)
        self.assertEqual(resolver.url_name, 'ai-jobs-cancel')

    def test_timesheet_suggestions_list_url(self):
        """Test timesheet suggestions list URL resolves correctly."""
        url = reverse('timesheet-suggestions-list')
        self.assertEqual(url, '/api/ai/timesheet-suggestions/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, SmartTimesheetSuggestionViewSet)
        self.assertEqual(resolver.url_name, 'timesheet-suggestions-list')

    def test_timesheet_suggestions_generate_url(self):
        """Test timesheet suggestions generate action URL resolves correctly."""
        url = reverse('timesheet-suggestions-generate-for-date')
        self.assertEqual(url, '/api/ai/timesheet-suggestions/generate_for_date/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, SmartTimesheetSuggestionViewSet)
        self.assertEqual(resolver.url_name, 'timesheet-suggestions-generate-for-date')

    def test_timesheet_suggestions_respond_url(self):
        """Test timesheet suggestions respond action URL resolves correctly."""
        url = reverse('timesheet-suggestions-respond', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/timesheet-suggestions/1/respond/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, SmartTimesheetSuggestionViewSet)
        self.assertEqual(resolver.url_name, 'timesheet-suggestions-respond')

    def test_task_assignments_list_url(self):
        """Test task assignments list URL resolves correctly."""
        url = reverse('task-assignments-list')
        self.assertEqual(url, '/api/ai/task-assignments/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, TaskAssignmentRecommendationViewSet)
        self.assertEqual(resolver.url_name, 'task-assignments-list')

    def test_task_assignments_generate_url(self):
        """Test task assignments generate action URL resolves correctly."""
        url = reverse('task-assignments-generate-for-task')
        self.assertEqual(url, '/api/ai/task-assignments/generate_for_task/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, TaskAssignmentRecommendationViewSet)
        self.assertEqual(resolver.url_name, 'task-assignments-generate-for-task')

    def test_task_assignments_respond_url(self):
        """Test task assignments respond action URL resolves correctly."""
        url = reverse('task-assignments-respond', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/task-assignments/1/respond/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, TaskAssignmentRecommendationViewSet)
        self.assertEqual(resolver.url_name, 'task-assignments-respond')

    def test_ai_insights_list_url(self):
        """Test AI insights list URL resolves correctly."""
        url = reverse('ai-insights-list')
        self.assertEqual(url, '/api/ai/insights/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIInsightViewSet)
        self.assertEqual(resolver.url_name, 'ai-insights-list')

    def test_ai_insights_generate_url(self):
        """Test AI insights generate action URL resolves correctly."""
        url = reverse('ai-insights-generate-for-workspace')
        self.assertEqual(url, '/api/ai/insights/generate_for_workspace/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIInsightViewSet)
        self.assertEqual(resolver.url_name, 'ai-insights-generate-for-workspace')

    def test_ai_insights_acknowledge_url(self):
        """Test AI insights acknowledge action URL resolves correctly."""
        url = reverse('ai-insights-acknowledge', kwargs={'pk': '1'})
        self.assertEqual(url, '/api/ai/insights/1/acknowledge/')

        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AIInsightViewSet)
        self.assertEqual(resolver.url_name, 'ai-insights-acknowledge')


class AIServicesURLAccessTest(APITestCase):
    """Test URL access and authentication for ai_services app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access AI services endpoints."""
        urls = [
            reverse('ai-models-list'),
            reverse('ai-jobs-list'),
            reverse('timesheet-suggestions-list'),
            reverse('task-assignments-list'),
            reverse('ai-insights-list'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"URL {url} should require authentication"
            )

    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access AI services endpoints."""
        self.client.force_authenticate(user=self.user)

        urls = [
            reverse('ai-models-list'),
            reverse('ai-jobs-list'),
            reverse('timesheet-suggestions-list'),
            reverse('task-assignments-list'),
            reverse('ai-insights-list'),
        ]

        for url in urls:
            response = self.client.get(url)
            # Should return 200 OK or 404 if no data exists
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND],
                f"URL {url} should be accessible to authenticated users"
            )