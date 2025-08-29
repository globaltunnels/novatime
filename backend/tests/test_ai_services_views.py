import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ai_services.models import (
    AIModel, AIJob, SmartTimesheetSuggestion,
    TaskAssignmentRecommendation, AIInsight
)
from organizations.models import Organization, Workspace
from projects.models import Project
from tasks.models import Task
from time_entries.models import TimeEntry
import datetime
from unittest.mock import patch, MagicMock

User = get_user_model()


class AIModelViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.ai_model = AIModel.objects.create(
            name='Test Model',
            model_type='timesheet_generation',
            version='1.0',
            status='active'
        )

        self.client.force_authenticate(user=self.user)

    def test_list_active_models(self):
        """Test listing active AI models."""
        url = reverse('aimodel-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Model')

    def test_retrieve_model(self):
        """Test retrieving a specific AI model."""
        url = reverse('aimodel-detail', kwargs={'pk': self.ai_model.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Model')

    def test_inactive_models_not_listed(self):
        """Test that inactive models are not listed."""
        self.ai_model.status = 'inactive'
        self.ai_model.save()

        url = reverse('aimodel-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class AIJobViewSetTest(APITestCase):
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

        self.ai_model = AIModel.objects.create(
            name='Test Model',
            model_type='timesheet_generation',
            version='1.0',
            status='active'
        )

        self.ai_job = AIJob.objects.create(
            user=self.user,
            workspace=self.workspace,
            model=self.ai_model,
            job_type='timesheet_generation',
            status='pending'
        )

        self.client.force_authenticate(user=self.user)

    def test_list_user_jobs(self):
        """Test listing user's AI jobs."""
        url = reverse('aijob-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_job(self):
        """Test creating a new AI job."""
        url = reverse('aijob-list')
        data = {
            'job_type': 'timesheet_generation',
            'workspace': str(self.workspace.id),
            'priority': 'medium',
            'input_data': {'test': 'data'}
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AIJob.objects.count(), 2)

    def test_cancel_pending_job(self):
        """Test cancelling a pending job."""
        url = reverse('aijob-cancel', kwargs={'pk': self.ai_job.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ai_job.refresh_from_db()
        self.assertEqual(self.ai_job.status, 'cancelled')

    def test_cancel_completed_job_fails(self):
        """Test that cancelling a completed job fails."""
        self.ai_job.status = 'completed'
        self.ai_job.save()

        url = reverse('aijob-cancel', kwargs={'pk': self.ai_job.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workspace_filtering(self):
        """Test filtering jobs by workspace."""
        url = reverse('aijob-list')
        response = self.client.get(url, {'workspace': str(self.workspace.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class SmartTimesheetSuggestionViewSetTest(APITestCase):
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

        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project'
        )

        self.task = Task.objects.create(
            project=self.project,
            title='Test Task'
        )

        self.suggestion = SmartTimesheetSuggestion.objects.create(
            user=self.user,
            workspace=self.workspace,
            suggestion_type='pattern_based',
            date=datetime.date(2023, 1, 1),
            project=self.project,
            task=self.task,
            suggested_start_time=datetime.time(9, 0),
            suggested_end_time=datetime.time(17, 0),
            suggested_duration_minutes=480,
            suggested_description='Test task',
            confidence_score=0.95
        )

        self.client.force_authenticate(user=self.user)

    def test_list_suggestions(self):
        """Test listing user's suggestions."""
        url = reverse('smarttimesheetsuggestion-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('ai_services.services.SmartTimesheetService.generate_suggestions_for_user')
    def test_generate_suggestions_for_date(self, mock_generate):
        """Test generating suggestions for a specific date."""
        mock_suggestion = MagicMock()
        mock_generate.return_value = [mock_suggestion]

        url = reverse('smarttimesheetsuggestion-generate-for-date')
        data = {
            'workspace': str(self.workspace.id),
            'date': '2023-01-01'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_generate.assert_called_once()

    def test_generate_suggestions_missing_data(self):
        """Test generating suggestions with missing data."""
        url = reverse('smarttimesheetsuggestion-generate-for-date')
        data = {'workspace': str(self.workspace.id)}  # Missing date

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_respond_to_suggestion_accept(self):
        """Test accepting a suggestion."""
        url = reverse('smarttimesheetsuggestion-respond', kwargs={'pk': self.suggestion.pk})
        data = {'action': 'accept', 'feedback': 'Good suggestion'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.status, 'accept')
        self.assertIsNotNone(self.suggestion.generated_time_entry)

    def test_respond_to_suggestion_modify(self):
        """Test modifying a suggestion."""
        url = reverse('smarttimesheetsuggestion-respond', kwargs={'pk': self.suggestion.pk})
        data = {
            'action': 'modify',
            'modified_start_time': '10:00:00',
            'modified_description': 'Modified task'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.status, 'modified')
        self.assertEqual(self.suggestion.suggested_start_time, datetime.time(10, 0))

    def test_respond_to_completed_suggestion_fails(self):
        """Test that responding to a completed suggestion fails."""
        self.suggestion.status = 'accept'
        self.suggestion.save()

        url = reverse('smarttimesheetsuggestion-respond', kwargs={'pk': self.suggestion.pk})
        data = {'action': 'accept'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskAssignmentRecommendationViewSetTest(APITestCase):
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

        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project',
            manager=self.user
        )

        self.task = Task.objects.create(
            project=self.project,
            title='Test Task'
        )

        self.recommendation = TaskAssignmentRecommendation.objects.create(
            task=self.task,
            project=self.project,
            workspace=self.workspace,
            recommendation_type='skill_based',
            recommended_assignee=self.user,
            confidence_score=0.88
        )

        self.client.force_authenticate(user=self.user)

    def test_list_recommendations(self):
        """Test listing task assignment recommendations."""
        url = reverse('taskassignmentrecommendation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('ai_services.services.TaskAssignmentService.recommend_assignee')
    def test_generate_recommendation_for_task(self, mock_recommend):
        """Test generating recommendation for a task."""
        mock_recommend.return_value = self.recommendation

        url = reverse('taskassignmentrecommendation-generate-for-task')
        data = {'task_id': str(self.task.id)}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_recommend.assert_called_once_with(self.task)

    def test_generate_recommendation_missing_task_id(self):
        """Test generating recommendation with missing task_id."""
        url = reverse('taskassignmentrecommendation-generate-for-task')
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_respond_to_recommendation_accept(self):
        """Test accepting a recommendation."""
        url = reverse('taskassignmentrecommendation-respond', kwargs={'pk': self.recommendation.pk})
        data = {'action': 'accept', 'feedback': 'Good recommendation'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.recommendation.refresh_from_db()
        self.assertEqual(self.recommendation.status, 'accepted')
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.user)

    def test_respond_to_recommendation_select_alternative(self):
        """Test selecting an alternative assignee."""
        alternative_user = User.objects.create_user(
            username='altuser',
            email='alt@example.com',
            password='testpass123'
        )

        url = reverse('taskassignmentrecommendation-respond', kwargs={'pk': self.recommendation.pk})
        data = {
            'action': 'select_alternative',
            'alternative_user_id': str(alternative_user.id)
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, alternative_user)


class AIInsightViewSetTest(APITestCase):
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

        self.insight = AIInsight.objects.create(
            insight_type='productivity_trend',
            workspace=self.workspace,
            user=self.user,
            title='Productivity Insight',
            description='User productivity increased',
            severity='medium',
            confidence_score=0.92
        )

        self.client.force_authenticate(user=self.user)

    def test_list_insights(self):
        """Test listing AI insights."""
        url = reverse('aiinsight-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('ai_services.services.AIInsightService.generate_productivity_insights')
    def test_generate_insights_for_workspace(self, mock_generate):
        """Test generating insights for a workspace."""
        mock_insights = [self.insight]
        mock_generate.return_value = mock_insights

        url = reverse('aiinsight-generate-for-workspace')
        data = {'workspace': str(self.workspace.id)}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_generate.assert_called_once_with(self.workspace, self.user)

    def test_generate_insights_missing_workspace(self):
        """Test generating insights with missing workspace."""
        url = reverse('aiinsight-generate-for-workspace')
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_acknowledge_insight(self):
        """Test acknowledging an insight."""
        url = reverse('aiinsight-acknowledge', kwargs={'pk': self.insight.pk})
        data = {'acknowledge': True}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.insight.refresh_from_db()
        self.assertTrue(self.insight.is_acknowledged)
        self.assertEqual(self.insight.acknowledged_by, self.user)

    def test_acknowledge_insight_with_false(self):
        """Test acknowledging insight with false value fails."""
        url = reverse('aiinsight-acknowledge', kwargs={'pk': self.insight.pk})
        data = {'acknowledge': False}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)