"""
Views for time entries app.

This module contains API views for managing time entries, timers,
idle periods, and related functionality.
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
    TimeEntry, Timer, IdlePeriod, TimeEntryTemplate, TimeEntryComment
)
from .serializers import (
    TimeEntrySerializer, TimeEntryCreateSerializer, TimerSerializer,
    TimerCreateSerializer, IdlePeriodSerializer, TimeEntryTemplateSerializer,
    TimeEntryTemplateCreateSerializer, TimeEntryCommentSerializer,
    TimerActionSerializer, TimeEntryBulkActionSerializer,
    TimeEntryReportSerializer, TimeTrackingStatsSerializer,
    TimerStatsSerializer, TimeEntryApprovalSerializer,
    TimeEntryFromTemplateSerializer
)


class TimeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntry model."""

    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Filter time entries by current user's workspaces."""
        return TimeEntry.objects.filter(
            workspace__organization__users=self.request.user,
            is_active=True
        ).prefetch_related(
            'user', 'workspace', 'task', 'project', 'approved_by'
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimeEntryCreateSerializer
        return TimeEntrySerializer

    def perform_create(self, serializer):
        """Create time entry."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a time entry."""
        time_entry = self.get_object()
        serializer = TimeEntryApprovalSerializer(data=request.data)

        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')

            if action == 'approve':
                time_entry.approve(request.user, notes)
                message = _('Time entry approved.')
            else:  # reject
                time_entry.reject(request.user, notes)
                message = _('Time entry rejected.')

            serializer = self.get_serializer(time_entry)
            return Response({
                'message': message,
                'time_entry': serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for the time entry."""
        time_entry = self.get_object()
        comments = time_entry.comments.all()
        serializer = TimeEntryCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to the time entry."""
        time_entry = self.get_object()
        serializer = TimeEntryCommentSerializer(
            data=request.data,
            context={'request': request, 'time_entry': time_entry}
        )

        if serializer.is_valid():
            comment = serializer.save()
            serializer = TimeEntryCommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def idle_periods(self, request, pk=None):
        """Get all idle periods for the time entry."""
        time_entry = self.get_object()
        idle_periods = time_entry.idle_periods.all()
        serializer = IdlePeriodSerializer(idle_periods, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def overlaps(self, request, pk=None):
        """Get overlapping time entries."""
        time_entry = self.get_object()
        overlaps = time_entry.get_overlap_entries()
        serializer = self.get_serializer(overlaps, many=True)
        return Response(serializer.data)


class TimerViewSet(viewsets.ModelViewSet):
    """ViewSet for Timer model."""

    serializer_class = TimerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter timers by current user."""
        return Timer.objects.filter(
            user=self.request.user,
            is_active=True
        ).prefetch_related('workspace', 'task', 'project')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimerCreateSerializer
        return TimerSerializer

    def perform_create(self, serializer):
        """Create timer."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def control(self, request, pk=None):
        """Control timer (pause, resume, stop)."""
        timer = self.get_object()
        serializer = TimerActionSerializer(data=request.data)

        if serializer.is_valid():
            action = serializer.validated_data['action']

            if action == 'pause':
                timer.pause()
                message = _('Timer paused.')
            elif action == 'resume':
                timer.resume()
                message = _('Timer resumed.')
            elif action == 'stop':
                time_entry = timer.stop()
                if time_entry:
                    message = _('Timer stopped and time entry created.')
                    return Response({
                        'message': message,
                        'time_entry': TimeEntrySerializer(time_entry).data
                    })
                else:
                    message = _('Timer stopped.')

            serializer = self.get_serializer(timer)
            return Response({
                'message': message,
                'timer': serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current running timer for user."""
        timer = Timer.objects.filter(
            user=request.user,
            status='running',
            is_active=True
        ).first()

        if timer:
            serializer = self.get_serializer(timer)
            return Response(serializer.data)
        else:
            return Response(
                {'message': _('No running timer found.')},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def quick_start(self, request):
        """Quick start a timer with minimal data."""
        serializer = TimerCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            timer = serializer.save()
            serializer = self.get_serializer(timer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IdlePeriodViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for IdlePeriod model."""

    serializer_class = IdlePeriodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter idle periods by current user's time entries."""
        return IdlePeriod.objects.filter(
            time_entry__user=self.request.user
        ).select_related('time_entry')


class TimeEntryTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryTemplate model."""

    serializer_class = TimeEntryTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates by current user or public templates."""
        return TimeEntryTemplate.objects.filter(
            Q(user=self.request.user) | Q(is_public=True),
            is_active=True
        ).prefetch_related('user', 'workspace')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimeEntryTemplateCreateSerializer
        return TimeEntryTemplateSerializer

    def perform_create(self, serializer):
        """Create template."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create a time entry from this template."""
        template = self.get_object()
        serializer = TimeEntryFromTemplateSerializer(data=request.data)

        if serializer.is_valid():
            # Get template data
            template_data = template.template_data.copy()

            # Override with request data
            overrides = serializer.validated_data
            template_data.update(overrides)

            # Set defaults from template
            if 'duration_minutes' not in template_data and template.default_duration_minutes:
                template_data['duration_minutes'] = template.default_duration_minutes
            if 'is_billable' not in template_data:
                template_data['is_billable'] = template.default_is_billable
            if 'hourly_rate' not in template_data and template.default_hourly_rate:
                template_data['hourly_rate'] = template.default_hourly_rate

            # Create time entry
            time_entry_serializer = TimeEntryCreateSerializer(
                data=template_data,
                context={'request': request}
            )

            if time_entry_serializer.is_valid():
                time_entry = time_entry_serializer.save()

                # Increment usage count
                template.usage_count += 1
                template.save()

                time_entry_serializer = TimeEntrySerializer(time_entry)
                return Response(time_entry_serializer.data, status=status.HTTP_201_CREATED)

            return Response(time_entry_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeEntryCommentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TimeEntryComment model."""

    serializer_class = TimeEntryCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter comments by current user's time entries."""
        return TimeEntryComment.objects.filter(
            time_entry__user=self.request.user
        ).select_related('time_entry', 'author')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_time_entry_action(request):
    """Perform bulk actions on multiple time entries."""
    serializer = TimeEntryBulkActionSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_ids = serializer.validated_data['time_entry_ids']
        action = serializer.validated_data['action']

        # Get time entries that user can access
        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            workspace__organization__users=request.user
        )

        updated_entries = []
        for time_entry in time_entries:
            try:
                if action == 'approve':
                    notes = serializer.validated_data.get('approval_notes', '')
                    time_entry.approve(request.user, notes)
                    updated_entries.append(time_entry)
                elif action == 'reject':
                    notes = serializer.validated_data.get('approval_notes', '')
                    time_entry.reject(request.user, notes)
                    updated_entries.append(time_entry)
                elif action == 'delete':
                    time_entry.is_active = False
                    time_entry.save()
                    updated_entries.append(time_entry)
                elif action == 'update_tags':
                    tags = serializer.validated_data['tags']
                    time_entry.tags = tags
                    time_entry.save()
                    updated_entries.append(time_entry)
            except Exception:
                # Skip entries that can't be updated
                continue

        serializer = TimeEntrySerializer(updated_entries, many=True)
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def time_entries_report(request):
    """Generate time entries report."""
    serializer = TimeEntryReportSerializer(data=request.query_params)

    if serializer.is_valid():
        # Build queryset based on filters
        queryset = TimeEntry.objects.filter(
            workspace__organization__users=request.user,
            is_active=True
        )

        filters = serializer.validated_data

        if 'workspace' in filters:
            queryset = queryset.filter(workspace_id=filters['workspace'])
        if 'user' in filters:
            queryset = queryset.filter(user_id=filters['user'])
        if 'task' in filters:
            queryset = queryset.filter(task_id=filters['task'])
        if 'project' in filters:
            queryset = queryset.filter(project_id=filters['project'])
        if 'start_date' in filters:
            queryset = queryset.filter(start_time__date__gte=filters['start_date'])
        if 'end_date' in filters:
            queryset = queryset.filter(start_time__date__lte=filters['end_date'])
        if 'is_billable' in filters:
            queryset = queryset.filter(is_billable=filters['is_billable'])
        if 'is_approved' in filters:
            queryset = queryset.filter(is_approved=filters['is_approved'])

        # Group results
        group_by = filters.get('group_by', 'user')
        include_idle = filters.get('include_idle_time', False)

        if group_by == 'user':
            report_data = queryset.values(
                'user__first_name', 'user__last_name'
            ).annotate(
                entry_count=Count('id'),
                total_minutes=Sum('duration_minutes'),
                billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
                total_cost=Sum('cost_amount'),
                idle_minutes=Sum('idle_minutes') if include_idle else 0
            ).order_by('-total_minutes')
        elif group_by == 'task':
            report_data = queryset.values(
                'task__title', 'task__key'
            ).annotate(
                entry_count=Count('id'),
                total_minutes=Sum('duration_minutes'),
                billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
                total_cost=Sum('cost_amount'),
                idle_minutes=Sum('idle_minutes') if include_idle else 0
            ).order_by('-total_minutes')
        elif group_by == 'project':
            report_data = queryset.values(
                'project__name', 'project__key'
            ).annotate(
                entry_count=Count('id'),
                total_minutes=Sum('duration_minutes'),
                billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
                total_cost=Sum('cost_amount'),
                idle_minutes=Sum('idle_minutes') if include_idle else 0
            ).order_by('-total_minutes')
        elif group_by == 'date':
            report_data = queryset.extra(
                select={'date': 'DATE(start_time)'}
            ).values('date').annotate(
                entry_count=Count('id'),
                total_minutes=Sum('duration_minutes'),
                billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
                total_cost=Sum('cost_amount'),
                idle_minutes=Sum('idle_minutes') if include_idle else 0
            ).order_by('date')

        return Response({'data': list(report_data)})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def time_tracking_stats(request):
    """Get time tracking statistics for user."""
    # Get date range (default to current month)
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    else:
        start_date = timezone.datetime.fromisoformat(start_date).date()

    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = timezone.datetime.fromisoformat(end_date).date()

    # Filter time entries
    time_entries = TimeEntry.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date,
        is_active=True
    )

    # Calculate statistics
    stats = time_entries.aggregate(
        total_entries=Count('id'),
        total_minutes=Sum('duration_minutes'),
        billable_minutes=Sum('duration_minutes', filter=Q(is_billable=True)),
        total_cost=Sum('cost_amount'),
        total_idle_minutes=Sum('idle_minutes'),
        avg_productivity=Avg('productivity_score'),
        avg_focus=Avg('focus_score')
    )

    # Calculate additional metrics
    total_hours = stats['total_minutes'] / 60 if stats['total_minutes'] else 0
    billable_hours = stats['billable_minutes'] / 60 if stats['billable_minutes'] else 0

    # Find most productive day
    daily_stats = time_entries.extra(
        select={'date': 'DATE(start_time)'}
    ).values('date').annotate(
        daily_minutes=Sum('duration_minutes'),
        daily_productivity=Avg('productivity_score')
    ).order_by('-daily_productivity')

    most_productive_day = daily_stats.first()['date'] if daily_stats else None

    # Find longest session
    longest_session = time_entries.order_by('-duration_minutes').first()
    longest_session_minutes = longest_session.duration_minutes if longest_session else 0

    # Calculate average session
    avg_session = stats['total_minutes'] / stats['total_entries'] if stats['total_entries'] else 0

    stats_data = {
        'total_entries': stats['total_entries'] or 0,
        'total_minutes': stats['total_minutes'] or 0,
        'total_hours': round(total_hours, 2),
        'billable_minutes': stats['billable_minutes'] or 0,
        'billable_hours': round(billable_hours, 2),
        'total_cost': round(stats['total_cost'] or 0, 2),
        'average_productivity_score': round(stats['avg_productivity'] or 0, 2),
        'average_focus_score': round(stats['avg_focus'] or 0, 2),
        'total_idle_minutes': stats['total_idle_minutes'] or 0,
        'most_productive_day': most_productive_day,
        'longest_session_minutes': longest_session_minutes,
        'average_session_minutes': round(avg_session, 2)
    }

    serializer = TimeTrackingStatsSerializer(stats_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timer_stats(request):
    """Get timer statistics for user."""
    # Get date range (default to current month)
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    else:
        start_date = timezone.datetime.fromisoformat(start_date).date()

    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = timezone.datetime.fromisoformat(end_date).date()

    # Get timers in date range
    timers = Timer.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=end_date,
        is_active=True
    )

    # Calculate statistics
    stats = timers.aggregate(
        total_timers=Count('id'),
        total_paused_minutes=Sum('total_paused_minutes')
    )

    # Get time entries created from timers
    time_entries_from_timers = TimeEntry.objects.filter(
        user=request.user,
        ai_generated=True,  # Assuming timer-created entries are marked as AI-generated
        start_time__date__gte=start_date,
        start_time__date__lte=end_date,
        is_active=True
    )

    timer_entries_stats = time_entries_from_timers.aggregate(
        total_minutes=Sum('duration_minutes'),
        avg_session=Avg('duration_minutes')
    )

    # Find most used task/project
    task_usage = time_entries_from_timers.values('task__title').annotate(
        count=Count('id')
    ).order_by('-count').first()

    project_usage = time_entries_from_timers.values('project__name').annotate(
        count=Count('id')
    ).order_by('-count').first()

    stats_data = {
        'total_timers_started': stats['total_timers'] or 0,
        'total_time_tracked_minutes': timer_entries_stats['total_minutes'] or 0,
        'average_session_minutes': round(timer_entries_stats['avg_session'] or 0, 2),
        'most_used_task': task_usage['task__title'] if task_usage else '',
        'most_used_project': project_usage['project__name'] if project_usage else '',
        'total_idle_time_minutes': stats['total_paused_minutes'] or 0,
        'auto_stop_events': 0,  # Would need to track this separately
        'manual_stop_events': stats['total_timers'] or 0
    }

    serializer = TimerStatsSerializer(stats_data)
    return Response(serializer.data)