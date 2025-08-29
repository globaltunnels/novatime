from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Timesheet, TimesheetEntry, TimesheetApproval,
    TimesheetException, TimesheetTemplate
)
from .serializers import (
    TimesheetSerializer, TimesheetEntrySerializer, TimesheetApprovalSerializer,
    TimesheetSubmissionSerializer, TimesheetApprovalActionSerializer,
    TimesheetTemplateSerializer, TimesheetGenerationSerializer,
    WeeklyTimesheetViewSerializer
)
from time_entries.models import TimeEntry
from projects.models import Project
from organizations.models import Workspace


class TimesheetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing timesheets with comprehensive CRUD operations.
    """
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter timesheets based on user permissions."""
        user = self.request.user
        queryset = Timesheet.objects.select_related(
            'user', 'workspace', 'submitted_by', 'approved_by'
        ).prefetch_related(
            'entries__project', 'entries__task',
            'approvals__approver', 'exceptions'
        )
        
        # Filter based on user role and permissions
        if user.is_superuser:
            return queryset
        
        # Users can see their own timesheets and ones they need to approve
        return queryset.filter(
            Q(user=user) | 
            Q(workspace__members=user, status='submitted')  # Assuming workspace has members
        ).distinct()
    
    def perform_create(self, serializer):
        """Set user and workspace when creating timesheet."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current_week(self, request):
        """Get current week's timesheet for the user."""
        user = request.user
        today = timezone.now().date()
        
        # Calculate start of week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Get workspace from query params
        workspace_id = request.query_params.get('workspace')
        if not workspace_id:
            return Response(
                {'error': 'Workspace parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response(
                {'error': 'Workspace not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create current week's timesheet
        timesheet, created = Timesheet.objects.get_or_create(
            user=user,
            workspace=workspace,
            start_date=start_of_week,
            end_date=end_of_week,
            defaults={
                'period_type': 'weekly',
                'status': 'draft'
            }
        )
        
        # Generate from time entries if newly created
        if created:
            self._generate_timesheet_from_entries(timesheet)
        
        serializer = WeeklyTimesheetViewSerializer(timesheet, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit timesheet for approval."""
        timesheet = self.get_object()
        
        # Check permissions
        if timesheet.user != request.user:
            return Response(
                {'error': 'You can only submit your own timesheets'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TimesheetSubmissionSerializer(
            data=request.data,
            context={'timesheet': timesheet}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                # Update timesheet status
                timesheet.status = 'submitted'
                timesheet.submitted_at = timezone.now()
                timesheet.submitted_by = request.user
                if serializer.validated_data.get('notes'):
                    timesheet.notes = serializer.validated_data['notes']
                timesheet.save()
                
                # Recalculate totals
                self._recalculate_timesheet_totals(timesheet)
                
                # Create approval record for managers
                self._create_approval_records(timesheet)
            
            return Response({'message': 'Timesheet submitted successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve or reject timesheet."""
        timesheet = self.get_object()
        
        # Check permissions - user should be able to approve others' timesheets
        if timesheet.user == request.user:
            return Response(
                {'error': 'You cannot approve your own timesheet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if timesheet.status != 'submitted':
            return Response(
                {'error': 'Only submitted timesheets can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TimesheetApprovalActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action_type = serializer.validated_data['action']
            comments = serializer.validated_data.get('comments', '')
            
            with transaction.atomic():
                # Get or create approval record
                approval, created = TimesheetApproval.objects.get_or_create(
                    timesheet=timesheet,
                    approver=request.user,
                    defaults={'status': 'pending'}
                )
                
                # Update approval based on action
                if action_type == 'approve':
                    approval.status = 'approved'
                    timesheet.status = 'approved'
                    timesheet.approved_at = timezone.now()
                    timesheet.approved_by = request.user
                elif action_type == 'reject':
                    approval.status = 'rejected'
                    timesheet.status = 'rejected'
                    timesheet.rejection_reason = comments
                elif action_type == 'request_changes':
                    approval.status = 'changes_requested'
                    timesheet.status = 'draft'  # Back to draft for changes
                    timesheet.rejection_reason = comments
                
                approval.comments = comments
                approval.decided_at = timezone.now()
                
                # Handle approved hours if provided
                if 'approved_hours' in serializer.validated_data:
                    approval.approved_hours = serializer.validated_data['approved_hours']
                
                approval.save()
                timesheet.save()
            
            return Response({'message': f'Timesheet {action_type}d successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def generate_from_entries(self, request, pk=None):
        """Generate timesheet entries from time tracking entries."""
        timesheet = self.get_object()
        
        if timesheet.user != request.user:
            return Response(
                {'error': 'You can only generate entries for your own timesheets'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # Clear existing entries if requested
            if request.data.get('clear_existing', False):
                timesheet.entries.all().delete()
            
            entries_created = self._generate_timesheet_from_entries(timesheet)
            self._recalculate_timesheet_totals(timesheet)
        
        return Response({
            'message': f'Generated {entries_created} timesheet entries',
            'entries_created': entries_created
        })
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get timesheets pending approval for current user."""
        user = request.user
        
        # Get timesheets that need approval from this user
        pending_timesheets = Timesheet.objects.filter(
            status='submitted'
        ).exclude(user=user).select_related(
            'user', 'workspace'
        ).prefetch_related('entries')
        
        # Filter by workspace permissions (simplified - in real app use proper permissions)
        workspace_id = request.query_params.get('workspace')
        if workspace_id:
            pending_timesheets = pending_timesheets.filter(workspace_id=workspace_id)
        
        serializer = TimesheetSerializer(
            pending_timesheets, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly_view(self, request):
        """Get weekly timesheet view with daily breakdowns."""
        user = request.user
        week_start = request.query_params.get('week_start')
        workspace_id = request.query_params.get('workspace')
        
        if not week_start:
            return Response(
                {'error': 'week_start parameter is required (YYYY-MM-DD format)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get timesheet for the week
        timesheet_filter = {
            'user': user,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if workspace_id:
            timesheet_filter['workspace_id'] = workspace_id
        
        try:
            timesheet = Timesheet.objects.get(**timesheet_filter)
            serializer = WeeklyTimesheetViewSerializer(
                timesheet, 
                context={'request': request}
            )
            return Response(serializer.data)
        except Timesheet.DoesNotExist:
            return Response({
                'timesheet': None,
                'message': 'No timesheet found for this week'
            })
    
    def _generate_timesheet_from_entries(self, timesheet):
        """Generate timesheet entries from time tracking entries."""
        entries_created = 0
        
        # Get time entries for the period
        time_entries = TimeEntry.objects.filter(
            user=timesheet.user,
            workspace=timesheet.workspace,
            start_time__date__range=[timesheet.start_date, timesheet.end_date]
        ).select_related('project', 'task')
        
        # Group by date, project, and task
        grouped_entries = {}
        for entry in time_entries:
            entry_date = entry.start_time.date()
            key = (entry_date, entry.project.id, entry.task.id if entry.task else None)
            if key not in grouped_entries:
                grouped_entries[key] = {
                    'date': entry_date,
                    'project': entry.project,
                    'task': entry.task,
                    'total_minutes': 0,
                    'descriptions': [],
                    'is_billable': entry.is_billable,
                    'source_entries': []
                }
            
            # Add duration
            if entry.duration_minutes:
                grouped_entries[key]['total_minutes'] += entry.duration_minutes
            
            if entry.description:
                grouped_entries[key]['descriptions'].append(entry.description)
            grouped_entries[key]['source_entries'].append(entry)
        
        # Create timesheet entries
        for entry_data in grouped_entries.values():
            if entry_data['total_minutes'] > 0:
                hours = Decimal(str(entry_data['total_minutes'] / 60))
                timesheet_entry, created = TimesheetEntry.objects.get_or_create(
                    timesheet=timesheet,
                    date=entry_data['date'],
                    project=entry_data['project'],
                    task=entry_data['task'],
                    defaults={
                        'hours': hours,
                        'description': '; '.join(entry_data['descriptions'][:3]),  # Limit descriptions
                        'is_billable': entry_data['is_billable']
                    }
                )
                
                if created:
                    # Link source time entries
                    timesheet_entry.source_time_entries.set(entry_data['source_entries'])
                    entries_created += 1
        
        return entries_created
    
    def _recalculate_timesheet_totals(self, timesheet):
        """Recalculate timesheet totals from entries."""
        entries = timesheet.entries.all()
        
        total_hours = sum(entry.hours for entry in entries)
        billable_hours = sum(entry.hours for entry in entries if entry.is_billable)
        
        # Calculate overtime (simplified - over 40 hours per week)
        overtime_hours = max(Decimal('0.00'), total_hours - Decimal('40.00'))
        
        timesheet.total_hours = total_hours
        timesheet.billable_hours = billable_hours
        timesheet.overtime_hours = overtime_hours
        timesheet.save()
    
    def _create_approval_records(self, timesheet):
        """Create approval records for managers/supervisors."""
        # This would be implemented based on your organization structure
        # For now, we'll create a placeholder approval record
        # In a real implementation, you'd determine who needs to approve based on:
        # - Organization hierarchy
        # - Project managers
        # - Department heads
        pass


class TimesheetEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual timesheet entries.
    """
    serializer_class = TimesheetEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter entries based on user permissions."""
        user = self.request.user
        return TimesheetEntry.objects.filter(
            timesheet__user=user
        ).select_related('timesheet', 'project', 'task')
    
    def perform_create(self, serializer):
        """Validate and create timesheet entry."""
        timesheet_id = self.request.data.get('timesheet')
        try:
            timesheet = Timesheet.objects.get(id=timesheet_id, user=self.request.user)
            serializer.save(timesheet=timesheet)
            
            # Recalculate timesheet totals
            self._recalculate_timesheet_totals(timesheet)
        except Timesheet.DoesNotExist:
            raise serializers.ValidationError("Invalid timesheet or permission denied")
    
    def perform_update(self, serializer):
        """Update entry and recalculate totals."""
        instance = serializer.save()
        self._recalculate_timesheet_totals(instance.timesheet)
    
    def perform_destroy(self, instance):
        """Delete entry and recalculate totals."""
        timesheet = instance.timesheet
        instance.delete()
        self._recalculate_timesheet_totals(timesheet)
    
    def _recalculate_timesheet_totals(self, timesheet):
        """Recalculate timesheet totals from entries."""
        entries = timesheet.entries.all()
        
        total_hours = sum(entry.hours for entry in entries)
        billable_hours = sum(entry.hours for entry in entries if entry.is_billable)
        overtime_hours = max(Decimal('0.00'), total_hours - Decimal('40.00'))
        
        timesheet.total_hours = total_hours
        timesheet.billable_hours = billable_hours
        timesheet.overtime_hours = overtime_hours
        timesheet.save()


class TimesheetTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing timesheet templates.
    """
    serializer_class = TimesheetTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's templates."""
        return TimesheetTemplate.objects.filter(
            user=self.request.user
        ).order_by('-last_used', 'name')
    
    def perform_create(self, serializer):
        """Set user when creating template."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def apply_to_timesheet(self, request, pk=None):
        """Apply template to a timesheet."""
        template = self.get_object()
        timesheet_id = request.data.get('timesheet_id')
        
        try:
            timesheet = Timesheet.objects.get(id=timesheet_id, user=request.user)
        except Timesheet.DoesNotExist:
            return Response(
                {'error': 'Timesheet not found or permission denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if timesheet.status != 'draft':
            return Response(
                {'error': 'Can only apply templates to draft timesheets'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Apply template logic here
        # This would implement the template application based on template_data
        template.use_count += 1
        template.last_used = timezone.now()
        template.save()
        
        return Response({'message': 'Template applied successfully'})


class TimesheetReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for timesheet reports and analytics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get timesheet summary for a period."""
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        workspace_id = request.query_params.get('workspace')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build filter
        filter_kwargs = {
            'user': user,
            'start_date__gte': start_date,
            'end_date__lte': end_date
        }
        
        if workspace_id:
            filter_kwargs['workspace_id'] = workspace_id
        
        # Get timesheets in period
        timesheets = Timesheet.objects.filter(**filter_kwargs)
        
        # Calculate summary statistics
        summary = timesheets.aggregate(
            total_timesheets=Count('id'),
            total_hours=Sum('total_hours'),
            total_billable_hours=Sum('billable_hours'),
            total_overtime_hours=Sum('overtime_hours')
        )
        
        # Status breakdown
        status_breakdown = {}
        for status_choice in Timesheet.STATUS_CHOICES:
            status_key = status_choice[0]
            status_breakdown[status_key] = timesheets.filter(status=status_key).count()
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': summary,
            'status_breakdown': status_breakdown,
            'billable_percentage': (
                round((summary['total_billable_hours'] or 0) / (summary['total_hours'] or 1) * 100, 1)
                if summary['total_hours'] else 0
            )
        })