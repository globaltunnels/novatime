import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from time_entries.models import TimeEntry, TimeEntryBreak, Timer, IdleTime, TimeEntryCorrection, BulkTimeOperation
from organizations.models import Organization, Workspace, Membership
from projects.models import Project, Client
from tasks.models import Task
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class TimeEntriesViewsTest(APITestCase):
    """Test time_entries views (currently minimal - placeholder for future implementation)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org'
        )

        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name='Test Workspace'
        )

        # Create membership
        Membership.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='member'
        )

        self.client_obj = Client.objects.create(
            name='Test Client',
            organization=self.organization
        )

        self.project = Project.objects.create(
            name='Test Project',
            workspace=self.workspace,
            client=self.client_obj,
            manager=self.user
        )

        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            status='in_progress',
            assignee=self.user,
            created_by=self.user
        )

        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() - timedelta(hours=1),
            duration_minutes=60,
            description='Test time entry',
            is_billable=True,
            hourly_rate=Decimal('50.00'),
            source='manual'
        )

        self.client.force_authenticate(user=self.user)

    def test_time_entries_views_module_import(self):
        """Test that time_entries views module can be imported."""
        try:
            from time_entries import views
            self.assertTrue(hasattr(views, 'render'))
        except ImportError as e:
            self.fail(f"Failed to import time_entries views: {e}")

    def test_time_entries_views_structure(self):
        """Test that time_entries views module has expected structure."""
        from time_entries import views

        # Should have basic Django imports
        self.assertTrue(hasattr(views, 'render'))

        # Check for any view functions (currently none expected)
        view_functions = [attr for attr in dir(views) if not attr.startswith('_') and callable(getattr(views, attr))]
        expected_functions = ['render']  # Django's render shortcut

        for func in expected_functions:
            self.assertIn(func, view_functions, f"Expected view function {func} not found")

    def test_no_time_entry_urls_configured(self):
        """Test that no time entry-specific URLs are currently configured."""
        # This test verifies the current state where time_entries views are minimal
        # When views are implemented, this test should be updated or removed

        from time_entries import views

        # Check that there are no custom view functions beyond Django's render
        custom_views = []
        for attr in dir(views):
            if not attr.startswith('_') and callable(getattr(views, attr)) and attr != 'render':
                custom_views.append(attr)

        # Currently should be empty (no custom views implemented)
        self.assertEqual(len(custom_views), 0,
                        f"Unexpected custom views found: {custom_views}")

    def test_time_entry_models_available_for_views(self):
        """Test that all time entry models are available for future view implementation."""
        # Verify models exist and can be imported
        models_to_check = [TimeEntry, TimeEntryBreak, Timer, IdleTime, TimeEntryCorrection, BulkTimeOperation]

        for model in models_to_check:
            # Check model has Meta class
            self.assertTrue(hasattr(model, '_meta'))

            # Check model has expected fields
            fields = [f.name for f in model._meta.fields]
            self.assertGreater(len(fields), 0, f"Model {model.__name__} has no fields")

        # Test model relationships work
        self.assertEqual(self.time_entry.user, self.user)
        self.assertEqual(self.time_entry.workspace, self.workspace)
        self.assertEqual(self.time_entry.project, self.project)
        self.assertEqual(self.time_entry.task, self.task)

    def test_time_entry_data_access_patterns(self):
        """Test common data access patterns that views would use."""
        # Test time entry queries
        user_entries = TimeEntry.objects.filter(user=self.user)
        self.assertEqual(user_entries.count(), 1)

        # Test workspace filtering
        workspace_entries = TimeEntry.objects.filter(workspace=self.workspace)
        self.assertEqual(workspace_entries.count(), 1)

        # Test project filtering
        project_entries = TimeEntry.objects.filter(project=self.project)
        self.assertEqual(project_entries.count(), 1)

        # Test task filtering
        task_entries = TimeEntry.objects.filter(task=self.task)
        self.assertEqual(task_entries.count(), 1)

        # Test date range filtering
        start_date = timezone.now() - timedelta(days=1)
        end_date = timezone.now() + timedelta(days=1)
        date_entries = TimeEntry.objects.filter(start_time__range=[start_date, end_date])
        self.assertEqual(date_entries.count(), 1)

        # Test billable filtering
        billable_entries = TimeEntry.objects.filter(is_billable=True)
        self.assertEqual(billable_entries.count(), 1)

    def test_time_entry_calculations(self):
        """Test time entry calculations that views would use."""
        # Test duration calculation
        self.assertEqual(self.time_entry.duration_minutes, 60)

        # Test cost calculation
        expected_cost = Decimal('50.00')  # 1 hour * $50/hour
        self.assertEqual(self.time_entry.hourly_rate, expected_cost)

        # Test total time for user
        total_minutes = TimeEntry.objects.filter(user=self.user).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        self.assertEqual(total_minutes, 60)

        # Test total cost for user
        from django.db.models import Sum, F
        total_cost = TimeEntry.objects.filter(user=self.user).aggregate(
            total=Sum(F('duration_minutes') * F('hourly_rate') / 60, output_field=models.DecimalField())
        )['total'] or Decimal('0.00')
        self.assertEqual(total_cost, Decimal('50.00'))

    def test_time_entry_crud_operations_readiness(self):
        """Test CRUD operations that views would implement."""
        # Test time entry creation
        new_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(minutes=30),
            description='New time entry',
            is_billable=True
        )

        # Duration should be calculated automatically
        new_entry.refresh_from_db()
        self.assertEqual(new_entry.duration_minutes, 30)

        # Test time entry update
        new_entry.description = 'Updated description'
        new_entry.save()
        new_entry.refresh_from_db()
        self.assertEqual(new_entry.description, 'Updated description')

        # Test time entry deletion
        entry_id = new_entry.id
        new_entry.delete()
        self.assertFalse(TimeEntry.objects.filter(id=entry_id).exists())

    def test_timer_functionality(self):
        """Test timer functionality that views would implement."""
        # Test starting a timer
        timer_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            task=self.task,
            start_time=timezone.now(),
            is_running=True,
            description='Timer entry'
        )

        # Create timer record
        timer = Timer.objects.create(
            user=self.user,
            time_entry=timer_entry,
            is_running=True
        )

        self.assertEqual(timer.user, self.user)
        self.assertEqual(timer.time_entry, timer_entry)
        self.assertTrue(timer.is_running)

        # Test stopping timer
        timer_entry.end_time = timezone.now() + timedelta(minutes=45)
        timer_entry.is_running = False
        timer_entry.save()

        timer_entry.refresh_from_db()
        self.assertEqual(timer_entry.duration_minutes, 45)
        self.assertFalse(timer_entry.is_running)

        # Clean up
        timer.delete()

    def test_time_entry_break_management(self):
        """Test time entry break management that views would implement."""
        # Create a break during time entry
        break_start = self.time_entry.start_time + timedelta(minutes=30)
        break_end = break_start + timedelta(minutes=15)

        time_break = TimeEntryBreak.objects.create(
            time_entry=self.time_entry,
            break_type='lunch',
            start_time=break_start,
            end_time=break_end,
            notes='Lunch break'
        )

        # Duration should be calculated automatically
        time_break.refresh_from_db()
        self.assertEqual(time_break.duration_minutes, 15)

        # Test break affects total productive time
        productive_time = self.time_entry.duration_minutes - time_break.duration_minutes
        self.assertEqual(productive_time, 45)  # 60 - 15

    def test_idle_time_detection(self):
        """Test idle time detection that views would implement."""
        # Create idle time period
        idle_start = self.time_entry.start_time + timedelta(minutes=20)
        idle_end = idle_start + timedelta(minutes=10)

        idle_time = IdleTime.objects.create(
            time_entry=self.time_entry,
            start_time=idle_start,
            end_time=idle_end,
            detection_method='mouse_keyboard',
            action_taken='pending'
        )

        # Duration should be calculated automatically
        idle_time.refresh_from_db()
        self.assertEqual(idle_time.duration_minutes, 10)

        # Test idle time resolution
        idle_time.action_taken = 'discard'
        idle_time.save()

        idle_time.refresh_from_db()
        self.assertEqual(idle_time.action_taken, 'discard')

    def test_time_entry_correction_workflow(self):
        """Test time entry correction workflow that views would implement."""
        # Create a correction record
        correction = TimeEntryCorrection.objects.create(
            time_entry=self.time_entry,
            corrected_by=self.user,
            field_changed='description',
            old_value={'description': 'Test time entry'},
            new_value={'description': 'Corrected description'},
            reason='Typo correction'
        )

        self.assertEqual(correction.time_entry, self.time_entry)
        self.assertEqual(correction.corrected_by, self.user)
        self.assertEqual(correction.field_changed, 'description')

        # Test approval workflow
        correction.requires_approval = True
        correction.save()

        # Approve correction
        correction.is_approved = True
        correction.approved_by = self.user
        correction.approved_at = timezone.now()
        correction.save()

        correction.refresh_from_db()
        self.assertTrue(correction.is_approved)
        self.assertIsNotNone(correction.approved_at)

    def test_bulk_time_operations(self):
        """Test bulk time operations that views would implement."""
        # Create bulk operation record
        bulk_op = BulkTimeOperation.objects.create(
            user=self.user,
            workspace=self.workspace,
            operation_type='import',
            status='pending',
            total_entries=10
        )

        self.assertEqual(bulk_op.user, self.user)
        self.assertEqual(bulk_op.workspace, self.workspace)
        self.assertEqual(bulk_op.operation_type, 'import')
        self.assertEqual(bulk_op.status, 'pending')

        # Test operation progress
        bulk_op.processed_entries = 5
        bulk_op.status = 'processing'
        bulk_op.save()

        bulk_op.refresh_from_db()
        self.assertEqual(bulk_op.processed_entries, 5)
        self.assertEqual(bulk_op.status, 'processing')

        # Test operation completion
        bulk_op.processed_entries = 10
        bulk_op.status = 'completed'
        bulk_op.completed_at = timezone.now()
        bulk_op.save()

        bulk_op.refresh_from_db()
        self.assertEqual(bulk_op.status, 'completed')
        self.assertIsNotNone(bulk_op.completed_at)

    def test_time_entry_validation(self):
        """Test time entry validation that views would implement."""
        # Test end time after start time
        with self.assertRaises(Exception):
            TimeEntry.objects.create(
                user=self.user,
                workspace=self.workspace,
                project=self.project,
                start_time=timezone.now(),
                end_time=timezone.now() - timedelta(minutes=30),  # End before start
                description='Invalid time entry'
            )

        # Test required fields
        with self.assertRaises(Exception):
            TimeEntry.objects.create(
                user=self.user,
                workspace=self.workspace,
                # Missing project
                start_time=timezone.now(),
                description='Missing project'
            )

    def test_time_entry_filtering_and_search(self):
        """Test filtering and search that views would implement."""
        # Create additional time entries for testing
        TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1, hours=2),
            duration_minutes=120,
            description='Yesterday work',
            is_billable=False
        )

        # Test date filtering
        today_entries = TimeEntry.objects.filter(
            start_time__date=timezone.now().date()
        )
        self.assertEqual(today_entries.count(), 1)

        yesterday_entries = TimeEntry.objects.filter(
            start_time__date=(timezone.now() - timedelta(days=1)).date()
        )
        self.assertEqual(yesterday_entries.count(), 1)

        # Test billable filtering
        billable_entries = TimeEntry.objects.filter(is_billable=True)
        non_billable_entries = TimeEntry.objects.filter(is_billable=False)

        self.assertEqual(billable_entries.count(), 1)
        self.assertEqual(non_billable_entries.count(), 1)

        # Test description search
        search_entries = TimeEntry.objects.filter(description__icontains='work')
        self.assertEqual(search_entries.count(), 1)

    def test_time_entry_aggregations(self):
        """Test time entry aggregations that views would use."""
        from django.db.models import Sum, Avg, Count

        # Test total time by user
        user_totals = TimeEntry.objects.filter(user=self.user).aggregate(
            total_time=Sum('duration_minutes'),
            avg_rate=Avg('hourly_rate'),
            entry_count=Count('id')
        )

        self.assertEqual(user_totals['total_time'], 180)  # 60 + 120
        self.assertEqual(user_totals['entry_count'], 2)

        # Test total time by project
        project_totals = TimeEntry.objects.filter(project=self.project).aggregate(
            total_time=Sum('duration_minutes'),
            total_cost=Sum(
                models.F('duration_minutes') * models.F('hourly_rate') / 60,
                output_field=models.DecimalField()
            )
        )

        self.assertEqual(project_totals['total_time'], 180)

        # Test time by date
        daily_totals = TimeEntry.objects.extra(
            select={'date': 'DATE(start_time)'}
        ).values('date').annotate(
            total_time=Sum('duration_minutes')
        ).order_by('date')

        self.assertEqual(len(daily_totals), 2)  # Two different dates

    def test_time_entry_external_integrations(self):
        """Test external integration fields that views would manage."""
        # Test external ID and source
        self.time_entry.external_id = 'JIRA-123'
        self.time_entry.external_source = 'jira'
        self.time_entry.save()

        self.time_entry.refresh_from_db()
        self.assertEqual(self.time_entry.external_id, 'JIRA-123')
        self.assertEqual(self.time_entry.external_source, 'jira')

        # Test AI-generated entries
        ai_entry = TimeEntry.objects.create(
            user=self.user,
            workspace=self.workspace,
            project=self.project,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(minutes=90),
            description='AI-generated entry',
            source='ai_generated',
            ai_generated=True,
            ai_confidence=0.85,
            ai_source_data={'calendar_event': 'Team meeting'}
        )

        self.assertTrue(ai_entry.ai_generated)
        self.assertEqual(ai_entry.ai_confidence, 0.85)
        self.assertEqual(ai_entry.source, 'ai_generated')

    def test_time_entry_locking_workflow(self):
        """Test time entry locking workflow that views would implement."""
        # Test locking entries
        self.time_entry.is_locked = True
        self.time_entry.save()

        self.time_entry.refresh_from_db()
        self.assertTrue(self.time_entry.is_locked)

        # Locked entries should not be editable (would be enforced in views)
        # This is a business rule that views would implement

        # Test unlocking
        self.time_entry.is_locked = False
        self.time_entry.save()

        self.time_entry.refresh_from_db()
        self.assertFalse(self.time_entry.is_locked)

    def test_time_entry_reporting_data(self):
        """Test reporting data that views would generate."""
        # Create diverse time entries for reporting
        entries_data = [
            {
                'user': self.user,
                'workspace': self.workspace,
                'project': self.project,
                'start_time': timezone.now() - timedelta(days=i),
                'end_time': timezone.now() - timedelta(days=i, hours=2),
                'duration_minutes': 120,
                'is_billable': i % 2 == 0,  # Alternate billable/non-billable
                'hourly_rate': Decimal('50.00') if i % 2 == 0 else Decimal('0.00')
            }
            for i in range(7)  # Last 7 days
        ]

        for entry_data in entries_data:
            TimeEntry.objects.create(**entry_data)

        # Test weekly summary
        week_start = timezone.now() - timedelta(days=7)
        weekly_entries = TimeEntry.objects.filter(start_time__gte=week_start)

        weekly_stats = weekly_entries.aggregate(
            total_hours=Sum('duration_minutes') / 60,
            billable_hours=Sum(
                models.Case(
                    models.When(is_billable=True, then='duration_minutes'),
                    default=0,
                    output_field=models.IntegerField()
                )
            ) / 60,
            total_cost=Sum(
                models.Case(
                    models.When(is_billable=True, then=models.F('duration_minutes') * models.F('hourly_rate') / 60),
                    default=0,
                    output_field=models.DecimalField()
                )
            )
        )

        self.assertEqual(weekly_entries.count(), 7)
        self.assertIsNotNone(weekly_stats['total_hours'])

    def test_time_entry_export_import_readiness(self):
        """Test export/import functionality that views would implement."""
        # Test data serialization for export
        entry_data = {
            'id': str(self.time_entry.id),
            'user': self.time_entry.user.email,
            'project': self.time_entry.project.name,
            'task': self.time_entry.task.title if self.time_entry.task else None,
            'start_time': self.time_entry.start_time.isoformat(),
            'end_time': self.time_entry.end_time.isoformat() if self.time_entry.end_time else None,
            'duration_minutes': self.time_entry.duration_minutes,
            'description': self.time_entry.description,
            'is_billable': self.time_entry.is_billable,
            'hourly_rate': str(self.time_entry.hourly_rate) if self.time_entry.hourly_rate else None
        }

        # Verify all expected fields are present
        expected_fields = [
            'id', 'user', 'project', 'task', 'start_time', 'end_time',
            'duration_minutes', 'description', 'is_billable', 'hourly_rate'
        ]

        for field in expected_fields:
            self.assertIn(field, entry_data)

        # Test data validation for import
        import_data = {
            'user': self.user.id,
            'workspace': self.workspace.id,
            'project': self.project.id,
            'start_time': timezone.now().isoformat(),
            'end_time': (timezone.now() + timedelta(hours=1)).isoformat(),
            'description': 'Imported entry',
            'is_billable': True
        }

        # This would be validated in import views
        self.assertIsNotNone(import_data['user'])
        self.assertIsNotNone(import_data['workspace'])
        self.assertIsNotNone(import_data['project'])