"""
Views for timesheets app.

This module contains API views for managing timesheets, periods,
approvals, and related functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Timesheet, TimesheetPeriod, TimesheetEntry, ApprovalWorkflow,
    TimesheetComment, TimesheetTemplate
)
from .serializers import (
    TimesheetSerializer, TimesheetCreateSerializer,
    TimesheetPeriodSerializer, TimesheetPeriodCreateSerializer,
    TimesheetEntrySerializer, TimesheetEntryCreateSerializer,
    ApprovalWorkflowSerializer, ApprovalWorkflowCreateSerializer,
    TimesheetCommentSerializer, TimesheetCommentCreateSerializer,
    TimesheetTemplateSerializer, TimesheetTemplateCreateSerializer,
    TimesheetBulkActionSerializer, TimesheetReportSerializer,
    TimesheetSummarySerializer, TimesheetTransitionSerializer
)


class TimesheetPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for TimesheetPeriod model."""

    serializer_class = TimesheetPeriodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter periods by current user's workspaces."""
        return TimesheetPeriod.objects.filter(
            workspace__organization__users=self.request.user,
            is_active=True
        ).prefetch_related('workspace', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimesheetPeriodCreateSerializer
        return TimesheetPeriodSerializer

    def perform_create(self, serializer):
        """Create period with current user as creator."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a timesheet period."""
        period = self.get_object()
        period.is_active = False
        period.save()

        serializer = self.get_serializer(period)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timesheets(self, request, pk=None):
        """Get all timesheets for the period."""
        period = self.get_object()
        timesheets = period.timesheets.filter(is_active=True)
        serializer = TimesheetSerializer(timesheets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_timesheets(self, request, pk=None):
        """Create timesheets for all users in the workspace."""
        period = self.get_object()
        workspace = period.workspace

        # Get all active users in the workspace
        users = workspace.memberships.filter(is_active=True).values_list('user', flat=True)

        created_timesheets = []
        for user_id in users:
            # Check if timesheet already exists
            existing = Timesheet.objects.filter(
                user_id=user_id,
                period=period
            ).first()

            if not existing:
                timesheet = Timesheet.objects.create(
                    user_id=user_id,
                    workspace=workspace,
                    period=period
                )
                created_timesheets.append(timesheet)

        serializer = TimesheetSerializer(created_timesheets, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TimesheetViewSet(viewsets.ModelViewSet):
    """ViewSet for Timesheet model."""

    serializer_class = TimesheetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter timesheets by current user's workspaces."""
        return Timesheet.objects.filter(
            workspace__organization__users=self.request.user,
            is_active=True
        ).prefetch_related(
            'user', 'workspace', 'period', 'approved_by',
            'approval_workflow'
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimesheetCreateSerializer
        return TimesheetSerializer

    def perform_create(self, serializer):
        """Create timesheet with current user."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """Transition timesheet to a new status."""
        timesheet = self.get_object()
        serializer = TimesheetTransitionSerializer(data=request.data)

        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            comment_text = serializer.validated_data.get('comment', '')
            rejection_reason = serializer.validated_data.get('rejection_reason', '')

            # Update timesheet status
            old_status = timesheet.status

            if new_status == 'submitted':
                timesheet.submit()
            elif new_status == 'approved':
                timesheet.approve(request.user)
            elif new_status == 'rejected':
                timesheet.reject(request.user, rejection_reason)

            # Create comment for status change
            if comment_text:
                TimesheetComment.objects.create(
                    timesheet=timesheet,
                    author=request.user,
                    content=comment_text,
                    comment_type='system'
                )

            # Create system comment for status transition
            TimesheetComment.objects.create(
                timesheet=timesheet,
                author=request.user,
                content=f"Status changed from {old_status} to {new_status}",
                comment_type='system'
            )

            serializer = self.get_serializer(timesheet)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """Get all entries for the timesheet."""
        timesheet = self.get_object()
        entries = timesheet.entries.all()
        serializer = TimesheetEntrySerializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_entry(self, request, pk=None):
        """Add a time entry to the timesheet."""
        timesheet = self.get_object()
        serializer = TimesheetEntryCreateSerializer(
            data=request.data,
            context={'timesheet': timesheet}
        )

        if serializer.is_valid():
            entry = serializer.save()
            serializer = TimesheetEntrySerializer(entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_entry(self, request, pk=None):
        """Remove a time entry from the timesheet."""
        timesheet = self.get_object()
        entry_id = request.data.get('entry_id')

        if not entry_id:
            return Response(
                {'error': _('Entry ID is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        entry = get_object_or_404(
            TimesheetEntry,
            id=entry_id,
            timesheet=timesheet
        )

        entry.delete()
        return Response({'message': _('Entry removed from timesheet.')})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for the timesheet."""
        timesheet = self.get_object()
        comments = timesheet.comments.all()
        serializer = TimesheetCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to the timesheet."""
        timesheet = self.get_object()
        serializer = TimesheetCommentCreateSerializer(
            data=request.data,
            context={'request': request, 'timesheet': timesheet}
        )

        if serializer.is_valid():
            comment = serializer.save()
            serializer = TimesheetCommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate totals for the timesheet."""
        timesheet = self.get_object()
        timesheet.save()  # This triggers the _calculate_totals method

        serializer = self.get_serializer(timesheet)
        return Response(serializer.data)


class TimesheetEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for TimesheetEntry model."""

    serializer_class = TimesheetEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter entries by current user's timesheets."""
        return TimesheetEntry.objects.filter(
            timesheet__workspace__organization__users=self.request.user
        ).select_related('timesheet', 'time_entry')


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for ApprovalWorkflow model."""

    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter workflows by current user's workspaces."""
        return ApprovalWorkflow.objects.filter(
            workspace__organization__users=self.request.user,
            is_active=True
        ).prefetch_related('workspace', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ApprovalWorkflowCreateSerializer
        return ApprovalWorkflowSerializer

    def perform_create(self, serializer):
        """Create workflow with current user as creator."""
        serializer.save()


class TimesheetCommentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TimesheetComment model."""

    serializer_class = TimesheetCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter comments by current user's timesheets."""
        return TimesheetComment.objects.filter(
            timesheet__workspace__organization__users=self.request.user
        ).select_related('timesheet', 'author')


class TimesheetTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for TimesheetTemplate model."""

    serializer_class = TimesheetTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates by current user's workspaces."""
        return TimesheetTemplate.objects.filter(
            workspace__organization__users=self.request.user,
            is_active=True
        ).prefetch_related('workspace', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimesheetTemplateCreateSerializer
        return TimesheetTemplateSerializer

    def perform_create(self, serializer):
        """Create template with current user."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create a timesheet from this template."""
        template = self.get_object()

        # Get template data
        template_data = template.template_data.copy()

        # Override period if specified
        period_id = request.data.get('period_id')
        if period_id:
            template_data['period'] = period_id

        # Create timesheet from template
        serializer = TimesheetCreateSerializer(
            data=template_data,
            context={'request': request}
        )

        if serializer.is_valid():
            timesheet = serializer.save()

            # Increment usage count
            template.usage_count += 1
            template.save()

            timesheet_serializer = TimesheetSerializer(timesheet)
            return Response(timesheet_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_timesheet_action(request):
    """Perform bulk actions on multiple timesheets."""
    serializer = TimesheetBulkActionSerializer(data=request.data)

    if serializer.is_valid():
        timesheet_ids = serializer.validated_data['timesheet_ids']
        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')

        # Get timesheets that user has access to
        timesheets = Timesheet.objects.filter(
            id__in=timesheet_ids,
            workspace__organization__users=request.user
        )

        updated_timesheets = []
        for timesheet in timesheets:
            try:
                if action == 'submit':
                    if timesheet.status == 'draft':
                        timesheet.submit()
                        updated_timesheets.append(timesheet)
                elif action == 'approve':
                    if timesheet.status == 'submitted':
                        timesheet.approve(request.user)
                        updated_timesheets.append(timesheet)
                elif action == 'reject':
                    if timesheet.status == 'submitted':
                        timesheet.reject(request.user, reason)
                        updated_timesheets.append(timesheet)
            except ValueError:
                # Skip timesheets that can't transition
                continue

        serializer = TimesheetSerializer(updated_timesheets, many=True)
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheets_report(request):
    """Generate timesheets report."""
    serializer = TimesheetReportSerializer(data=request.query_params)

    if serializer.is_valid():
        # Build queryset based on filters
        queryset = Timesheet.objects.filter(
            workspace__organization__users=request.user,
            is_active=True
        )

        filters = serializer.validated_data

        if 'workspace' in filters:
            queryset = queryset.filter(workspace_id=filters['workspace'])
        if 'period' in filters:
            queryset = queryset.filter(period_id=filters['period'])
        if 'user' in filters:
            queryset = queryset.filter(user_id=filters['user'])
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        if 'start_date' in filters:
            queryset = queryset.filter(period__start_date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(period__end_date__lte=filters['end_date'])

        # Group results
        group_by = filters.get('group_by', 'user')

        if group_by == 'user':
            report_data = queryset.values(
                'user__first_name', 'user__last_name'
            ).annotate(
                total_timesheets=Count('id'),
                submitted_timesheets=Count('id', filter=Q(status='submitted')),
                approved_timesheets=Count('id', filter=Q(status='approved')),
                total_hours=Sum('total_hours'),
                total_cost=Sum('total_cost')
            ).order_by('-total_hours')
        elif group_by == 'period':
            report_data = queryset.values(
                'period__name', 'period__start_date', 'period__end_date'
            ).annotate(
                total_timesheets=Count('id'),
                submitted_timesheets=Count('id', filter=Q(status='submitted')),
                approved_timesheets=Count('id', filter=Q(status='approved')),
                total_hours=Sum('total_hours'),
                total_cost=Sum('total_cost')
            ).order_by('-period__start_date')
        elif group_by == 'status':
            report_data = queryset.values('status').annotate(
                count=Count('id'),
                total_hours=Sum('total_hours'),
                total_cost=Sum('total_cost')
            ).order_by('-count')
        elif group_by == 'workspace':
            report_data = queryset.values('workspace__name').annotate(
                total_timesheets=Count('id'),
                submitted_timesheets=Count('id', filter=Q(status='submitted')),
                approved_timesheets=Count('id', filter=Q(status='approved')),
                total_hours=Sum('total_hours'),
                total_cost=Sum('total_cost')
            ).order_by('-total_hours')

        return Response({'data': list(report_data)})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timesheets_summary(request):
    """Get timesheets summary for workspace."""
    workspace_id = request.query_params.get('workspace_id')
    period_id = request.query_params.get('period_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    # Build base queryset
    queryset = Timesheet.objects.filter(
        workspace__organization__users=request.user,
        is_active=True
    )

    if workspace_id:
        queryset = queryset.filter(workspace_id=workspace_id)
    if period_id:
        queryset = queryset.filter(period_id=period_id)
    if start_date:
        queryset = queryset.filter(period__start_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(period__end_date__lte=end_date)

    # Calculate summary statistics
    summary = queryset.aggregate(
        total_timesheets=Count('id'),
        submitted_timesheets=Count('id', filter=Q(status='submitted')),
        approved_timesheets=Count('id', filter=Q(status='approved')),
        rejected_timesheets=Count('id', filter=Q(status='rejected')),
        total_hours=Sum('total_hours'),
        billable_hours=Sum('billable_hours'),
        total_cost=Sum('total_cost'),
        average_quality_score=Avg('quality_score')
    )

    # Calculate additional metrics
    total_timesheets = summary['total_timesheets'] or 0
    submitted_timesheets = summary['submitted_timesheets'] or 0

    if total_timesheets > 0:
        on_time_submission_rate = (submitted_timesheets / total_timesheets) * 100
    else:
        on_time_submission_rate = 0

    # Approval time calculation (simplified)
    approval_time_avg = 0
    approved_timesheets = queryset.filter(
        status='approved',
        submitted_at__isnull=False,
        approved_at__isnull=False
    )

    if approved_timesheets.exists():
        approval_times = []
        for timesheet in approved_timesheets:
            if timesheet.submitted_at and timesheet.approved_at:
                delta = timesheet.approved_at - timesheet.submitted_at
                approval_times.append(delta.total_seconds() / 3600)  # hours

        if approval_times:
            approval_time_avg = sum(approval_times) / len(approval_times)

    # Status breakdown
    status_breakdown = queryset.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    # Period breakdown
    period_breakdown = queryset.values(
        'period__name', 'period__start_date', 'period__end_date'
    ).annotate(
        count=Count('id')
    ).order_by('-period__start_date')[:10]

    # Top submitters
    top_submitters = queryset.values(
        'user__first_name', 'user__last_name'
    ).annotate(
        timesheet_count=Count('id'),
        total_hours=Sum('total_hours')
    ).order_by('-timesheet_count')[:10]

    # Quality issues summary
    quality_issues = {}
    for timesheet in queryset.exclude(quality_issues__isnull=True):
        for issue in timesheet.quality_issues:
            issue_type = issue.get('type', 'unknown')
            quality_issues[issue_type] = quality_issues.get(issue_type, 0) + 1

    summary_data = {
        **summary,
        'on_time_submission_rate': on_time_submission_rate,
        'approval_time_avg': approval_time_avg,
        'timesheets_by_status': {item['status']: item['count'] for item in status_breakdown},
        'timesheets_by_period': list(period_breakdown),
        'top_submitters': list(top_submitters),
        'quality_issues_summary': quality_issues
    }

    serializer = TimesheetSummarySerializer(summary_data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_timesheet_from_template(request, template_id):
    """Create a timesheet from a template."""
    try:
        template = TimesheetTemplate.objects.get(
            id=template_id,
            workspace__organization__users=request.user
        )
    except TimesheetTemplate.DoesNotExist:
        return Response(
            {'error': _('Template not found.')},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get template data
    template_data = template.template_data.copy()

    # Override with request data
    template_data.update(request.data)

    # Create timesheet from template
    serializer = TimesheetCreateSerializer(
        data=template_data,
        context={'request': request}
    )

    if serializer.is_valid():
        timesheet = serializer.save()

        # Increment usage count
        template.usage_count += 1
        template.save()

        timesheet_serializer = TimesheetSerializer(timesheet)
        return Response(timesheet_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)