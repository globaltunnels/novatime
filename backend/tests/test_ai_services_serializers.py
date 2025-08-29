import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from ai_services.models import (
    AIModel, AIJob, SmartTimesheetSuggestion,
    TaskAssignmentRecommendation, TaskAssignmentAlternative, AIInsight
)
from ai_services.serializers import (
    AIModelSerializer, AIJobSerializer, SmartTimesheetSuggestionSerializer,
    TimesheetSuggestionActionSerializer, TaskAssignmentRecommendationSerializer,
    TaskAssignmentAlternativeSerializer, TaskAssignmentActionSerializer,
    AIInsightSerializer, InsightAcknowledgeSerializer, AIJobCreateSerializer
)
from organizations.models import Organization, Workspace
from projects.models import Project
from tasks.models import Task
import datetime

User = get_user_model()


class AIModelSerializerTest(TestCase):
    def setUp(self):
        self.ai_model = AIModel.objects.create(
            name='Test Model',
            model_type='timesheet_generation',
            version='1.0',
            status='active',
            model_config={'param': 'value'}
        )

    def test_ai_model_serialization(self):
        """Test AIModel serialization."""
        serializer = AIModelSerializer(self.ai_model)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Model')
        self.assertEqual(data['model_type'], 'timesheet_generation')
        self.assertEqual(data['version'], '1.0')
        self.assertEqual(data['status'], 'active')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_ai_model_deserialization(self):
        """Test AIModel deserialization."""
        data = {
            'name': 'New Model',
            'model_type': 'task_assignment',
            'version': '2.0',
            'status': 'active',
            'model_config': {'new_param': 'new_value'}
        }

        serializer = AIModelSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        model = serializer.save()

        self.assertEqual(model.name, 'New Model')
        self.assertEqual(model.model_type, 'task_assignment')
        self.assertEqual(model.version, '2.0')


class AIJobSerializerTest(TestCase):
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
            version='1.0'
        )

        self.ai_job = AIJob.objects.create(
            user=self.user,
            workspace=self.workspace,
            model=self.ai_model,
            job_type='timesheet_generation',
            status='pending',
            input_data={'input': 'data'},
            output_data={'result': 'data'}
        )

    def test_ai_job_serialization(self):
        """Test AIJob serialization with related fields."""
        serializer = AIJobSerializer(self.ai_job)
        data = serializer.data

        self.assertEqual(data['job_type'], 'timesheet_generation')
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['user_name'], self.user.get_full_name())
        self.assertEqual(data['model_name'], 'Test Model')
        self.assertIn('input_data', data)
        self.assertIn('output_data', data)


class SmartTimesheetSuggestionSerializerTest(TestCase):
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
            title='Test Task',
            description='Test Description'
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
            confidence_score=0.95,
            reasoning='Test reasoning',
            source_data={'test': 'data'}
        )

    def test_smart_timesheet_suggestion_serialization(self):
        """Test SmartTimesheetSuggestion serialization."""
        serializer = SmartTimesheetSuggestionSerializer(self.suggestion)
        data = serializer.data

        self.assertEqual(data['suggestion_type'], 'pattern_based')
        self.assertEqual(data['suggested_description'], 'Test task')
        self.assertEqual(data['confidence_score'], 0.95)
        self.assertEqual(data['user_name'], self.user.get_full_name())
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['task_title'], 'Test Task')


class TimesheetSuggestionActionSerializerTest(TestCase):
    def test_accept_action_validation(self):
        """Test accept action validation."""
        data = {'action': 'accept', 'feedback': 'Good suggestion'}
        serializer = TimesheetSuggestionActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_reject_action_validation(self):
        """Test reject action validation."""
        data = {'action': 'reject', 'feedback': 'Not relevant'}
        serializer = TimesheetSuggestionActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_modify_action_validation_success(self):
        """Test modify action validation with required fields."""
        data = {
            'action': 'modify',
            'feedback': 'Adjust time',
            'modified_start_time': '10:00:00',
            'modified_end_time': '18:00:00'
        }
        serializer = TimesheetSuggestionActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_modify_action_validation_failure(self):
        """Test modify action validation without required fields."""
        data = {'action': 'modify', 'feedback': 'Adjust time'}
        serializer = TimesheetSuggestionActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class TaskAssignmentRecommendationSerializerTest(TestCase):
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
            title='Test Task',
            description='Test Description'
        )

        self.recommendation = TaskAssignmentRecommendation.objects.create(
            task=self.task,
            project=self.project,
            workspace=self.workspace,
            recommendation_type='skill_based',
            recommended_assignee=self.user,
            confidence_score=0.88,
            reasoning='Best match for skills',
            analysis_data={'skills': ['python', 'django']}
        )

    def test_task_assignment_recommendation_serialization(self):
        """Test TaskAssignmentRecommendation serialization."""
        serializer = TaskAssignmentRecommendationSerializer(self.recommendation)
        data = serializer.data

        self.assertEqual(data['recommendation_type'], 'skill_based')
        self.assertEqual(data['confidence_score'], 0.88)
        self.assertEqual(data['task_title'], 'Test Task')
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['recommended_assignee_name'], self.user.get_full_name())


class TaskAssignmentActionSerializerTest(TestCase):
    def test_accept_action_validation(self):
        """Test accept action validation."""
        data = {'action': 'accept', 'feedback': 'Good recommendation'}
        serializer = TaskAssignmentActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_select_alternative_action_validation_success(self):
        """Test select alternative action with user ID."""
        data = {
            'action': 'select_alternative',
            'alternative_user_id': '12345678-1234-5678-9012-123456789012'
        }
        serializer = TaskAssignmentActionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_select_alternative_action_validation_failure(self):
        """Test select alternative action without user ID."""
        data = {'action': 'select_alternative'}
        serializer = TaskAssignmentActionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('alternative_user_id', serializer.errors)


class AIInsightSerializerTest(TestCase):
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

        self.insight = AIInsight.objects.create(
            insight_type='productivity_trend',
            workspace=self.workspace,
            user=self.user,
            project=self.project,
            title='Productivity Insight',
            description='User productivity has increased by 15%',
            severity='medium',
            insight_data={'increase': 0.15},
            recommendations=['Continue current work patterns'],
            confidence_score=0.92,
            valid_until=datetime.date(2023, 12, 31)
        )

    def test_ai_insight_serialization(self):
        """Test AIInsight serialization."""
        serializer = AIInsightSerializer(self.insight)
        data = serializer.data

        self.assertEqual(data['insight_type'], 'productivity_trend')
        self.assertEqual(data['title'], 'Productivity Insight')
        self.assertEqual(data['severity'], 'medium')
        self.assertEqual(data['confidence_score'], 0.92)
        self.assertEqual(data['user_name'], self.user.get_full_name())
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['workspace_name'], 'Test Workspace')


class InsightAcknowledgeSerializerTest(TestCase):
    def test_acknowledge_true_validation(self):
        """Test acknowledge with True value."""
        data = {'acknowledge': True}
        serializer = InsightAcknowledgeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_acknowledge_false_validation_failure(self):
        """Test acknowledge with False value fails."""
        data = {'acknowledge': False}
        serializer = InsightAcknowledgeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('acknowledge', serializer.errors)


class AIJobCreateSerializerTest(APITestCase):
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

        self.client.force_authenticate(user=self.user)

    def test_ai_job_create_with_active_model(self):
        """Test AIJob creation with active model."""
        data = {
            'job_type': 'timesheet_generation',
            'workspace': str(self.workspace.id),
            'priority': 'medium',
            'input_data': {'test': 'data'}
        }

        serializer = AIJobCreateSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        job = serializer.save()

        self.assertEqual(job.job_type, 'timesheet_generation')
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.model, self.ai_model)
        self.assertEqual(job.workspace, self.workspace)

    def test_ai_job_create_without_active_model(self):
        """Test AIJob creation fails without active model."""
        # Deactivate the model
        self.ai_model.status = 'inactive'
        self.ai_model.save()

        data = {
            'job_type': 'timesheet_generation',
            'workspace': str(self.workspace.id),
            'priority': 'medium',
            'input_data': {'test': 'data'}
        }

        serializer = AIJobCreateSerializer(data=data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)