import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from ai_services.models import AIModel, AIJob, SmartTimesheetSuggestion

User = get_user_model()


class AIModelTest(TestCase):
    def test_ai_model_creation(self):
        model = AIModel.objects.create(
            name='Test Model',
            model_type='timesheet_generation',
            version='1.0',
            status='active',
            model_config={'param': 'value'}
        )
        
        self.assertEqual(model.name, 'Test Model')
        self.assertEqual(model.model_type, 'timesheet_generation')
        self.assertEqual(model.version, '1.0')
        self.assertEqual(model.status, 'active')
        self.assertEqual(model.model_config, {'param': 'value'})
        self.assertIsNotNone(model.created_at)
        
    def test_ai_model_string_representation(self):
        model = AIModel.objects.create(
            name='Test Model',
            model_type='timesheet_generation',
            version='1.0'
        )
        
        self.assertEqual(str(model), 'Test Model v1.0 (Timesheet Generation)')


class AIJobTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace
        from organizations.models import Organization, Workspace
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
        
    def test_ai_job_creation(self):
        job = AIJob.objects.create(
            user=self.user,
            workspace=self.workspace,
            model=self.ai_model,
            job_type='timesheet_generation',
            status='pending',
            input_data={'input': 'data'},
            output_data={'result': 'data'}
        )
        
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.workspace, self.workspace)
        self.assertEqual(job.model, self.ai_model)
        self.assertEqual(job.job_type, 'timesheet_generation')
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.input_data, {'input': 'data'})
        self.assertEqual(job.output_data, {'result': 'data'})
        self.assertIsNotNone(job.created_at)
        # Note: AIJob model doesn't have updated_at field
        
    def test_ai_job_string_representation(self):
        job = AIJob.objects.create(
            user=self.user,
            workspace=self.workspace,
            model=self.ai_model,
            job_type='timesheet_generation',
            status='completed'
        )
        
        self.assertEqual(
            str(job),
            f"Generate Timesheet - {job.status} ({self.user.email})"
        )


class SmartTimesheetSuggestionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization and workspace
        from organizations.models import Organization, Workspace
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )
        
        # Create project
        from projects.models import Project
        self.project = Project.objects.create(
            workspace=self.workspace,
            name='Test Project'
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
            status='completed'
        )
        
    def test_smart_timesheet_suggestion_creation(self):
        import datetime
        suggestion = SmartTimesheetSuggestion.objects.create(
            user=self.user,
            workspace=self.workspace,
            suggestion_type='pattern_based',
            date=datetime.date(2023, 1, 1),
            project=self.project,
            suggested_start_time=datetime.time(9, 0),
            suggested_end_time=datetime.time(17, 0),
            suggested_duration_minutes=480,
            suggested_description='Test task',
            confidence_score=0.95,
            reasoning='Test reasoning',
            source_data={'test': 'data'}
        )
        
        self.assertEqual(suggestion.user, self.user)
        self.assertEqual(suggestion.workspace, self.workspace)
        self.assertEqual(suggestion.suggestion_type, 'pattern_based')
        self.assertEqual(suggestion.date, datetime.date(2023, 1, 1))
        self.assertEqual(suggestion.project, self.project)
        self.assertEqual(suggestion.suggested_start_time, datetime.time(9, 0))
        self.assertEqual(suggestion.suggested_end_time, datetime.time(17, 0))
        self.assertEqual(suggestion.suggested_duration_minutes, 480)
        self.assertEqual(suggestion.suggested_description, 'Test task')
        self.assertEqual(suggestion.confidence_score, 0.95)
        self.assertEqual(suggestion.reasoning, 'Test reasoning')
        self.assertEqual(suggestion.source_data, {'test': 'data'})
        self.assertIsNotNone(suggestion.created_at)
        
    def test_smart_timesheet_suggestion_string_representation(self):
        import datetime
        suggestion = SmartTimesheetSuggestion.objects.create(
            user=self.user,
            workspace=self.workspace,
            suggestion_type='pattern_based',
            date=datetime.date(2023, 1, 1),
            project=self.project,
            suggested_start_time=datetime.time(9, 0),
            suggested_end_time=datetime.time(17, 0),
            suggested_duration_minutes=480,
            suggested_description='Test task',
            confidence_score=0.85,
            reasoning='Test reasoning',
            source_data={}
        )
        
        self.assertEqual(
            str(suggestion),
            f"Suggestion for {self.user.email} on 2023-01-01 - {self.project.name}"
        )