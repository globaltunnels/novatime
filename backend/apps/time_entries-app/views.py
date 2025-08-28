"""
Views for time_entries app.

This module contains API views for managing time entries, timers, approvals,
idle periods, templates, categories, tags, comments, attachments,
and related functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from .models import (
    TimeEntry, Timer, TimeEntryApproval, IdlePeriod, TimeEntryTemplate,
    TimeEntryCategory, TimeEntryTag, TimeEntryComment, TimeEntryAttachment
)
from .serializers import (
    TimeEntrySerializer, TimeEntryCreateSerializer, TimerSerializer,
    TimerCreateSerializer, TimeEntryApprovalSerializer,
    TimeEntryApprovalCreateSerializer, IdlePeriodSerializer,
    TimeEntryTemplateSerializer, TimeEntryCategorySerializer,
    TimeEntryTagSerializer, TimeEntryCommentSerializer,
    TimeEntryAttachmentSerializer, TimeEntryBulkActionSerializer,
    TimerActionSerializer, TimeEntryReportSerializer, TimeEntryStatsSerializer,
    TimerStatsSerializer, TimeEntryImportSerializer, TimeEntryExportSerializer,
    TimerSettingsSerializer, TimeEntryReminderSerializer,
    TimeEntryIntegrationSerializer, TimeEntryTemplateApplySerializer,
    TimeEntryDuplicateSerializer, TimeEntryMergeSerializer,
    TimeEntrySplitSerializer, TimeEntryLockSerializer, TimeEntryUnlockSerializer,
    TimeEntryAuditSerializer, TimeEntryAuditEntrySerializer,
    TimeEntryForecastSerializer, TimeEntryForecastResultSerializer,
    TimeEntryProductivitySerializer, TimeEntryProductivityResultSerializer,
    TimeEntryComplianceSerializer, TimeEntryComplianceResultSerializer,
    TimeEntryBackupSerializer, TimeEntryRestoreSerializer
)


class TimeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntry model."""

    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter time entries by current user's access."""
        return TimeEntry.objects.filter(
            Q(user=self.request.user) |
            Q(organization__users=self.request.user) |
            Q(workspace__memberships__user=self.request.user, workspace__memberships__is_active=True)
        ).distinct().prefetch_related('user', 'organization', 'workspace', 'project', 'task', 'approved_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimeEntryCreateSerializer
        return TimeEntrySerializer

    def perform_create(self, serializer):
        """Create time entry."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit time entry for approval."""
        time_entry = self.get_object()

        if not time_entry.can_user_edit(request.user):
            return Response(
                {'error': _('You don\'t have permission to submit this time entry.')},
                status=status.HTTP_403_FORBIDDEN
            )

        time_entry.submit_for_approval()
        serializer = self.get_serializer(time_entry)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve time entry."""
        time_entry = self.get_object()

        if not time_entry.can_user_approve(request.user):
            return Response(
                {'error': _('You don\'t have permission to approve this time entry.')},
                status=status.HTTP_403_FORBIDDEN
            )

        time_entry.approve(request.user)
        serializer = self.get_serializer(time_entry)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject time entry."""
        time_entry = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')

        if not time_entry.can_user_approve(request.user):
            return Response(
                {'error': _('You don\'t have permission to reject this time entry.')},
                status=status.HTTP_403_FORBIDDEN
            )

        time_entry.reject(rejection_reason, request.user)
        serializer = self.get_serializer(time_entry)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock time entry."""
        time_entry = self.get_object()

        if not time_entry.can_user_edit(request.user):
            return Response(
                {'error': _('You don\'t have permission to lock this time entry.')},
                status=status.HTTP_403_FORBIDDEN
            )

        time_entry.lock()
        serializer = self.get_serializer(time_entry)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on time entries."""
        serializer = TimeEntryBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            time_entry_ids = serializer.validated_data['time_entry_ids']
            action = serializer.validated_data['action']

            time_entries = TimeEntry.objects.filter(
                id__in=time_entry_ids,
                organization__users=request.user
            )

            updated_count = 0
            for time_entry in time_entries:
                if not time_entry.can_user_edit(request.user):
                    continue

                if action == 'submit':
                    time_entry.submit_for_approval()
                elif action == 'approve' and time_entry.can_user_approve(request.user):
                    time_entry.approve(request.user)
                elif action == 'reject' and time_entry.can_user_approve(request.user):
                    rejection_reason = serializer.validated_data.get('rejection_reason', '')
                    time_entry.reject(rejection_reason, request.user)
                elif action == 'update_status':
                    time_entry.status = serializer.validated_data['status']
                    time_entry.save()
                elif action == 'update_tags':
                    tags = serializer.validated_data['tags']
                    time_entry.tags = list(set(time_entry.tags + tags))
                    time_entry.save()
                elif action == 'update_categories':
                    categories = serializer.validated_data['categories']
                    time_entry.categories = list(set(time_entry.categories + categories))
                    time_entry.save()
                elif action == 'delete':
                    time_entry.delete()
                    continue

                updated_count += 1

            return Response({
                'message': _('Bulk action completed successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def report(self, request):
        """Generate time entry report."""
        serializer = TimeEntryReportSerializer(data=request.data)

        if serializer.is_valid():
            # Build queryset based on filters
            queryset = TimeEntry.objects.filter(
                organization__users=request.user
            )

            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']

            queryset = queryset.filter(
                start_time__date__gte=start_date,
                start_time__date__lte=end_date
            )

            if serializer.validated_data.get('user_ids'):
                queryset = queryset.filter(user_id__in=serializer.validated_data['user_ids'])

            if serializer.validated_data.get('project_ids'):
                queryset = queryset.filter(project_id__in=serializer.validated_data['project_ids'])

            if serializer.validated_data.get('task_ids'):
                queryset = queryset.filter(task_id__in=serializer.validated_data['task_ids'])

            if serializer.validated_data.get('organization_ids'):
                queryset = queryset.filter(organization_id__in=serializer.validated_data['organization_ids'])

            if serializer.validated_data.get('workspace_ids'):
                queryset = queryset.filter(workspace_id__in=serializer.validated_data['workspace_ids'])

            if serializer.validated_data.get('entry_types'):
                queryset = queryset.filter(entry_type__in=serializer.validated_data['entry_types'])

            if serializer.validated_data.get('statuses'):
                queryset = queryset.filter(status__in=serializer.validated_data['statuses'])

            if 'is_billable' in serializer.validated_data:
                queryset = queryset.filter(is_billable=serializer.validated_data['is_billable'])

            if serializer.validated_data.get('tags'):
                # Filter by tags (JSON field)
                tags_filter = Q()
                for tag in serializer.validated_data['tags']:
                    tags_filter |= Q(tags__contains=[tag])
                queryset = queryset.filter(tags_filter)

            if serializer.validated_data.get('categories'):
                # Filter by categories (JSON field)
                categories_filter = Q()
                for category in serializer.validated_data['categories']:
                    categories_filter |= Q(categories__contains=[category])
                queryset = queryset.filter(categories_filter)

            # Group results if requested
            group_by = serializer.validated_data.get('group_by', [])
            if group_by:
                results = self._group_time_entries(queryset, group_by)
            else:
                results = TimeEntrySerializer(queryset, many=True, context={'request': request}).data

            return Response({
                'count': queryset.count(),
                'results': results
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _group_time_entries(self, queryset, group_by):
        """Group time entries by specified fields."""
        groups = {}

        for entry in queryset:
            key_parts = []
            for field in group_by:
                if field == 'user':
                    key_parts.append(str(entry.user.id))
                elif field == 'project':
                    key_parts.append(str(entry.project.id) if entry.project else 'no_project')
                elif field == 'task':
                    key_parts.append(str(entry.task.id) if entry.task else 'no_task')
                elif field == 'date':
                    key_parts.append(entry.start_time.date().isoformat())
                elif field == 'week':
                    week_start = entry.start_time.date() - timedelta(days=entry.start_time.weekday())
                    key_parts.append(week_start.isoformat())
                elif field == 'month':
                    key_parts.append(entry.start_time.date().strftime('%Y-%m'))

            key = '|'.join(key_parts)

            if key not in groups:
                groups[key] = {
                    'group_key': key_parts,
                    'entries': [],
                    'total_hours': 0,
                    'total_cost': 0,
                    'count': 0
                }

            groups[key]['entries'].append(TimeEntrySerializer(entry, context={'request': self.request}).data)
            groups[key]['total_hours'] += float(entry.get_duration_hours())
            groups[key]['total_cost'] += float(entry.get_cost())
            groups[key]['count'] += 1

        return list(groups.values())

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get time entry statistics."""
        # Base queryset
        queryset = TimeEntry.objects.filter(
            organization__users=request.user
        )

        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)

        # Calculate statistics
        total_entries = queryset.count()
        total_hours = queryset.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        billable_entries = queryset.filter(is_billable=True)
        billable_hours = billable_entries.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        billable_percentage = (billable_hours / total_hours * 100) if total_hours > 0 else 0

        average_hours_per_entry = total_hours / total_entries if total_entries > 0 else 0

        total_cost = queryset.aggregate(
            total=Sum('cost_amount')
        )['total'] or 0

        average_cost_per_hour = total_cost / total_hours if total_hours > 0 else 0

        # Group by type
        entries_by_type = queryset.values('entry_type').annotate(
            count=Count('id'),
            hours=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        ).order_by('-count')

        # Group by status
        entries_by_status = queryset.values('status').annotate(
            count=Count('id'),
            hours=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        ).order_by('-count')

        # Hours by project
        hours_by_project = queryset.values('project__name').annotate(
            hours=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            )),
            count=Count('id')
        ).order_by('-hours')[:10]

        # Hours by user
        hours_by_user = queryset.values('user__email').annotate(
            hours=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            )),
            count=Count('id')
        ).order_by('-hours')[:10]

        # Hours by date (last 30 days)
        hours_by_date = queryset.filter(
            start_time__date__gte=timezone.now().date() - timedelta(days=30)
        ).values('start_time__date').annotate(
            hours=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            )),
            count=Count('id')
        ).order_by('start_time__date')

        # Top tags
        all_tags = []
        for entry in queryset:
            all_tags.extend(entry.tags)
        top_tags = [{'tag': tag, 'count': all_tags.count(tag)} for tag in set(all_tags)]
        top_tags.sort(key=lambda x: x['count'], reverse=True)[:10]

        # Top categories
        all_categories = []
        for entry in queryset:
            all_categories.extend(entry.categories)
        top_categories = [{'category': cat, 'count': all_categories.count(cat)} for cat in set(all_categories)]
        top_categories.sort(key=lambda x: x['count'], reverse=True)[:10]

        # Productivity trend (last 7 days)
        productivity_trend = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            day_entries = queryset.filter(start_time__date=date)
            day_hours = day_entries.aggregate(
                total=Sum(ExpressionWrapper(
                    F('duration_minutes') / 60,
                    output_field=fields.DecimalField()
                ))
            )['total'] or 0
            productivity_trend.append({
                'date': date.isoformat(),
                'hours': float(day_hours),
                'entries': day_entries.count()
            })

        # Cost trend (last 7 days)
        cost_trend = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            day_entries = queryset.filter(start_time__date=date)
            day_cost = day_entries.aggregate(
                total=Sum('cost_amount')
            )['total'] or 0
            cost_trend.append({
                'date': date.isoformat(),
                'cost': float(day_cost),
                'entries': day_entries.count()
            })

        stats = {
            'total_entries': total_entries,
            'total_hours': float(total_hours),
            'billable_hours': float(billable_hours),
            'billable_percentage': float(billable_percentage),
            'average_hours_per_entry': float(average_hours_per_entry),
            'total_cost': float(total_cost),
            'average_cost_per_hour': float(average_cost_per_hour),
            'entries_by_type': list(entries_by_type),
            'entries_by_status': list(entries_by_status),
            'hours_by_project': list(hours_by_project),
            'hours_by_user': list(hours_by_user),
            'hours_by_date': list(hours_by_date),
            'top_tags': top_tags,
            'top_categories': top_categories,
            'productivity_trend': productivity_trend,
            'cost_trend': cost_trend
        }

        serializer = TimeEntryStatsSerializer(stats)
        return Response(serializer.data)


class TimerViewSet(viewsets.ModelViewSet):
    """ViewSet for Timer model."""

    serializer_class = TimerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter timers by current user."""
        return Timer.objects.filter(
            user=self.request.user
        ).distinct().prefetch_related('project', 'task')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimerCreateSerializer
        return TimerSerializer

    def perform_create(self, serializer):
        """Create timer."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def action(self, request, pk=None):
        """Perform action on timer."""
        timer = self.get_object()
        serializer = TimerActionSerializer(data=request.data)

        if serializer.is_valid():
            action = serializer.validated_data['action']

            if action == 'start':
                timer.start()
            elif action == 'pause':
                timer.pause()
            elif action == 'resume':
                timer.resume()
            elif action == 'stop':
                timer.stop()

            response_serializer = self.get_serializer(timer)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_activity(self, request, pk=None):
        """Update timer activity."""
        timer = self.get_object()
        timer.update_activity()
        serializer = self.get_serializer(timer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active timers for current user."""
        timers = self.get_queryset().filter(status='running')
        serializer = self.get_serializer(timers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get timer statistics."""
        queryset = self.get_queryset()

        # Calculate statistics
        total_timers = queryset.count()
        active_timers = queryset.filter(status='running').count()
        paused_timers = queryset.filter(status='paused').count()
        stopped_timers = queryset.filter(status='stopped').count()

        # Total tracked hours
        total_tracked_hours = queryset.filter(status='stopped').aggregate(
            total=Sum(ExpressionWrapper(
                (F('end_time') - F('start_time')).seconds / 3600,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        # Average session length
        completed_timers = queryset.filter(status='stopped', end_time__isnull=False)
        if completed_timers.exists():
            avg_session = completed_timers.aggregate(
                avg=Avg(ExpressionWrapper(
                    (F('end_time') - F('start_time')).seconds / 60,
                    output_field=fields.DecimalField()
                ))
            )['avg'] or 0
        else:
            avg_session = 0

        # Most productive day/hour (simplified)
        most_productive_day = 'Monday'  # Would need real calculation
        most_productive_hour = 10  # Would need real calculation

        # Idle time
        idle_periods = IdlePeriod.objects.filter(timer__user=request.user)
        idle_time_total = idle_periods.aggregate(
            total=Sum('duration_seconds')
        )['total'] or 0
        idle_time_total = idle_time_total / 3600  # Convert to hours

        idle_time_percentage = (idle_time_total / total_tracked_hours * 100) if total_tracked_hours > 0 else 0

        # Timers by project
        timers_by_project = queryset.values('project__name').annotate(
            count=Count('id'),
            hours=Sum(ExpressionWrapper(
                (F('end_time') - F('start_time')).seconds / 3600,
                output_field=fields.DecimalField()
            )) if queryset.filter(end_time__isnull=False).exists() else 0
        ).order_by('-count')

        # Timers by user (just current user)
        timers_by_user = [{
            'user': request.user.get_full_name(),
            'count': total_timers,
            'hours': float(total_tracked_hours)
        }]

        # Productivity by day/hour (simplified)
        productivity_by_day = []
        for i in range(7):
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][i]
            productivity_by_day.append({
                'day': day_name,
                'hours': float(total_tracked_hours / 7)
            })

        productivity_by_hour = []
        for hour in range(24):
            productivity_by_hour.append({
                'hour': hour,
                'hours': float(total_tracked_hours / 24)
            })

        stats = {
            'total_timers': total_timers,
            'active_timers': active_timers,
            'paused_timers': paused_timers,
            'stopped_timers': stopped_timers,
            'total_tracked_hours': float(total_tracked_hours),
            'average_session_length': float(avg_session),
            'most_productive_day': most_productive_day,
            'most_productive_hour': most_productive_hour,
            'idle_time_total': float(idle_time_total),
            'idle_time_percentage': float(idle_time_percentage),
            'timers_by_project': list(timers_by_project),
            'timers_by_user': timers_by_user,
            'productivity_by_day': productivity_by_day,
            'productivity_by_hour': productivity_by_hour
        }

        serializer = TimerStatsSerializer(stats)
        return Response(serializer.data)


class TimeEntryApprovalViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryApproval model."""

    serializer_class = TimeEntryApprovalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter approvals by current user's access."""
        return TimeEntryApproval.objects.filter(
            Q(requested_by=self.request.user) |
            Q(approver=self.request.user) |
            Q(organization__users=self.request.user)
        ).distinct().prefetch_related('organization', 'workspace', 'approver', 'requested_by', 'time_entries')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TimeEntryApprovalCreateSerializer
        return TimeEntryApprovalSerializer

    def perform_create(self, serializer):
        """Create approval."""
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve the time entries."""
        approval = self.get_object()
        comments = request.data.get('comments', '')

        if approval.approver != request.user:
            return Response(
                {'error': _('You don\'t have permission to approve this request.')},
                status=status.HTTP_403_FORBIDDEN
            )

        approval.approve(comments)
        serializer = self.get_serializer(approval)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject the time entries."""
        approval = self.get_object()
        comments = request.data.get('comments', '')

        if approval.approver != request.user:
            return Response(
                {'error': _('You don\'t have permission to reject this request.')},
                status=status.HTTP_403_FORBIDDEN
            )

        approval.reject(comments)
        serializer = self.get_serializer(approval)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def partially_approve(self, request, pk=None):
        """Partially approve the time entries."""
        approval = self.get_object()
        approved_entries = request.data.get('approved_entries', [])
        rejected_entries = request.data.get('rejected_entries', [])
        comments = request.data.get('comments', '')

        if approval.approver != request.user:
            return Response(
                {'error': _('You don\'t have permission to approve this request.')},
                status=status.HTTP_403_FORBIDDEN
            )

        approval.partially_approve(approved_entries, rejected_entries, comments)
        serializer = self.get_serializer(approval)
        return Response(serializer.data)


class IdlePeriodViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for IdlePeriod model."""

    serializer_class = IdlePeriodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter idle periods by current user."""
        return IdlePeriod.objects.filter(
            user=self.request.user
        ).distinct().prefetch_related('timer')


class TimeEntryTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryTemplate model."""

    serializer_class = TimeEntryTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates by current user's organizations or public templates."""
        return TimeEntryTemplate.objects.filter(
            Q(organization__users=self.request.user) |
            Q(is_public=True)
        ).distinct().prefetch_related('organization', 'workspace', 'created_by')

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply template to create time entry."""
        template = self.get_object()
        serializer = TimeEntryTemplateApplySerializer(data=request.data)

        if serializer.is_valid():
            start_time = serializer.validated_data['start_time']
            duration_minutes = serializer.validated_data['duration_minutes']
            overrides = serializer.validated_data.get('overrides', {})

            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)

            # Build time entry data from template
            time_entry_data = {
                'user': request.user,
                'organization': template.organization or request.user.organization,
                'workspace': template.workspace or request.user.workspace,
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration_minutes,
                'entry_type': 'manual',
                'created_by': request.user
            }

            # Apply template data
            template_data = template.template_data
            time_entry_data.update({
                'description': template_data.get('description', ''),
                'is_billable': template_data.get('is_billable', True),
                'hourly_rate': template_data.get('hourly_rate'),
                'tags': template_data.get('tags', []),
                'categories': template_data.get('categories', []),
                'custom_fields': template_data.get('custom_fields', {})
            })

            # Apply overrides
            time_entry_data.update(overrides)

            # Create time entry
            time_entry = TimeEntry.objects.create(**time_entry_data)
            template.increment_usage()

            response_serializer = TimeEntrySerializer(time_entry, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeEntryCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryCategory model."""

    serializer_class = TimeEntryCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter categories by current user's organizations."""
        return TimeEntryCategory.objects.filter(
            organization__users=self.request.user
        ).distinct().prefetch_related('organization', 'created_by')


class TimeEntryTagViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryTag model."""

    serializer_class = TimeEntryTagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tags by current user's organizations."""
        return TimeEntryTag.objects.filter(
            organization__users=self.request.user
        ).distinct().prefetch_related('organization', 'created_by')


class TimeEntryCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryComment model."""

    serializer_class = TimeEntryCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter comments by current user's time entries."""
        return TimeEntryComment.objects.filter(
            time_entry__organization__users=self.request.user
        ).distinct().prefetch_related('time_entry', 'author', 'parent_comment')


class TimeEntryAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for TimeEntryAttachment model."""

    serializer_class = TimeEntryAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter attachments by current user's time entries."""
        return TimeEntryAttachment.objects.filter(
            time_entry__organization__users=self.request.user
        ).distinct().prefetch_related('time_entry', 'uploaded_by')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_time_entries(request):
    """Duplicate time entries."""
    serializer = TimeEntryDuplicateSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_ids = serializer.validated_data['time_entry_ids']
        date_offset_days = serializer.validated_data['date_offset_days']

        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            organization__users=request.user
        )

        duplicated_entries = []
        for time_entry in time_entries:
            if not time_entry.can_user_edit(request.user):
                continue

            # Calculate new dates
            new_start_time = time_entry.start_time + timedelta(days=date_offset_days)
            new_end_time = time_entry.end_time + timedelta(days=date_offset_days) if time_entry.end_time else None

            # Create duplicate
            duplicated_entry = TimeEntry.objects.create(
                user=time_entry.user,
                organization=time_entry.organization,
                workspace=time_entry.workspace,
                project=time_entry.project,
                task=time_entry.task,
                start_time=new_start_time,
                end_time=new_end_time,
                duration_minutes=time_entry.duration_minutes,
                description=f"[Duplicate] {time_entry.description}",
                entry_type=time_entry.entry_type,
                is_billable=time_entry.is_billable,
                hourly_rate=time_entry.hourly_rate,
                location=time_entry.location,
                tags=time_entry.tags,
                categories=time_entry.categories,
                custom_fields=time_entry.custom_fields,
                created_by=request.user
            )

            duplicated_entries.append(duplicated_entry)

        response_serializer = TimeEntrySerializer(duplicated_entries, many=True, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def merge_time_entries(request):
    """Merge time entries."""
    serializer = TimeEntryMergeSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_ids = serializer.validated_data['time_entry_ids']
        primary_entry_id = serializer.validated_data['primary_entry_id']

        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            organization__users=request.user
        )

        primary_entry = TimeEntry.objects.get(id=primary_entry_id)

        # Calculate merged data
        total_duration = sum(entry.duration_minutes for entry in time_entries)
        earliest_start = min(entry.start_time for entry in time_entries)
        latest_end = max(entry.end_time for entry in time_entries if entry.end_time)

        # Combine descriptions
        descriptions = [entry.description for entry in time_entries if entry.description]
        merged_description = ' | '.join(descriptions[:3])  # Limit to first 3

        # Update primary entry
        primary_entry.duration_minutes = total_duration
        primary_entry.end_time = latest_end
        primary_entry.description = merged_description
        primary_entry.save()

        # Delete other entries
        time_entries.exclude(id=primary_entry_id).delete()

        response_serializer = TimeEntrySerializer(primary_entry, context={'request': request})
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def split_time_entry(request):
    """Split time entry."""
    serializer = TimeEntrySplitSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_id = serializer.validated_data['time_entry_id']
        split_points = serializer.validated_data['split_points']
        descriptions = serializer.validated_data.get('descriptions', [])

        time_entry = TimeEntry.objects.get(
            id=time_entry_id,
            organization__users=request.user
        )

        if not time_entry.can_user_edit(request.user):
            return Response(
                {'error': _('You don\'t have permission to split this time entry.')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create split entries
        split_entries = []
        current_start = time_entry.start_time

        for i, duration in enumerate(split_points):
            split_end = current_start + timedelta(minutes=duration)

            split_entry = TimeEntry.objects.create(
                user=time_entry.user,
                organization=time_entry.organization,
                workspace=time_entry.workspace,
                project=time_entry.project,
                task=time_entry.task,
                start_time=current_start,
                end_time=split_end,
                duration_minutes=duration,
                description=descriptions[i] if i < len(descriptions) else f"Split {i+1}: {time_entry.description}",
                entry_type=time_entry.entry_type,
                is_billable=time_entry.is_billable,
                hourly_rate=time_entry.hourly_rate,
                location=time_entry.location,
                tags=time_entry.tags,
                categories=time_entry.categories,
                custom_fields=time_entry.custom_fields,
                created_by=request.user
            )

            split_entries.append(split_entry)
            current_start = split_end

        # Delete original entry
        time_entry.delete()

        response_serializer = TimeEntrySerializer(split_entries, many=True, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lock_time_entries(request):
    """Lock time entries."""
    serializer = TimeEntryLockSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_ids = serializer.validated_data['time_entry_ids']
        lock_reason = serializer.validated_data.get('lock_reason')

        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            organization__users=request.user
        )

        locked_count = 0
        for time_entry in time_entries:
            if time_entry.can_user_edit(request.user):
                time_entry.lock()
                locked_count += 1

        return Response({
            'message': _('Time entries locked successfully.'),
            'locked_count': locked_count
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlock_time_entries(request):
    """Unlock time entries."""
    serializer = TimeEntryUnlockSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_ids = serializer.validated_data['time_entry_ids']
        unlock_reason = serializer.validated_data.get('unlock_reason')

        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            organization__users=request.user
        )

        unlocked_count = 0
        for time_entry in time_entries:
            if time_entry.can_user_edit(request.user):
                time_entry.status = 'approved'  # Or appropriate status
                time_entry.save()
                unlocked_count += 1

        return Response({
            'message': _('Time entries unlocked successfully.'),
            'unlocked_count': unlocked_count
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def time_entry_audit(request):
    """Get time entry audit trail."""
    serializer = TimeEntryAuditSerializer(data=request.data)

    if serializer.is_valid():
        time_entry_id = serializer.validated_data['time_entry_id']

        # Get time entry
        time_entry = TimeEntry.objects.get(
            id=time_entry_id,
            organization__users=request.user
        )

        # Build audit trail (simplified - would need actual audit log)
        audit_entries = [
            {
                'timestamp': time_entry.created_at.isoformat(),
                'user': time_entry.created_by.get_full_name() if time_entry.created_by else 'System',
                'action': 'created',
                'field': 'time_entry',
                'old_value': None,
                'new_value': f"{time_entry.duration_minutes} minutes",
                'ip_address': time_entry.ip_address or 'unknown',
                'user_agent': time_entry.user_agent or 'unknown'
            }
        ]

        if time_entry.submitted_at:
            audit_entries.append({
                'timestamp': time_entry.submitted_at.isoformat(),
                'user': time_entry.user.get_full_name(),
                'action': 'submitted',
                'field': 'status',
                'old_value': 'draft',
                'new_value': 'submitted',
                'ip_address': time_entry.ip_address or 'unknown',
                'user_agent': time_entry.user_agent or 'unknown'
            })

        if time_entry.approved_at:
            audit_entries.append({
                'timestamp': time_entry.approved_at.isoformat(),
                'user': time_entry.approved_by.get_full_name() if time_entry.approved_by else 'System',
                'action': 'approved',
                'field': 'status',
                'old_value': 'submitted',
                'new_value': 'approved',
                'ip_address': 'system',
                'user_agent': 'system'
            })

        response_serializer = TimeEntryAuditEntrySerializer(audit_entries, many=True)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forecast_time_entries(request):
    """Forecast time entries."""
    serializer = TimeEntryForecastSerializer(data=request.data)

    if serializer.is_valid():
        forecast_days = serializer.validated_data['forecast_days']

        # Get historical data
        queryset = TimeEntry.objects.filter(
            user=request.user,
            start_time__date__gte=timezone.now().date() - timedelta(days=30)
        )

        # Simple forecasting based on average daily hours
        total_hours = queryset.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        avg_daily_hours = total_hours / 30 if 30 > 0 else 0

        # Generate forecast
        forecast_results = []
        for i in range(forecast_days):
            forecast_date = timezone.now().date() + timedelta(days=i + 1)
            predicted_hours = avg_daily_hours * 0.8  # Conservative estimate
            confidence_level = Decimal('0.75')  # Simplified confidence

            forecast_results.append({
                'forecast_date': forecast_date.isoformat(),
                'predicted_hours': float(predicted_hours),
                'confidence_level': float(confidence_level),
                'factors': ['historical average', 'user patterns'],
                'recommendations': ['Consider workload distribution']
            })

        response_serializer = TimeEntryForecastResultSerializer(forecast_results, many=True)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_productivity(request):
    """Analyze productivity."""
    serializer = TimeEntryProductivitySerializer(data=request.data)

    if serializer.is_valid():
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        # Get time entries for analysis
        queryset = TimeEntry.objects.filter(
            user=request.user,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        )

        # Calculate metrics
        total_hours = queryset.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        productive_entries = queryset.filter(is_billable=True)
        productive_hours = productive_entries.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        idle_periods = IdlePeriod.objects.filter(
            user=request.user,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        )
        idle_hours = idle_periods.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_seconds') / 3600,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        break_entries = queryset.filter(
            Q(description__icontains='break') |
            Q(description__icontains='lunch') |
            Q(categories__contains=['break'])
        )
        break_hours = break_entries.aggregate(
            total=Sum(ExpressionWrapper(
                F('duration_minutes') / 60,
                output_field=fields.DecimalField()
            ))
        )['total'] or 0

        # Calculate scores
        productivity_score = (productive_hours / total_hours * 100) if total_hours > 0 else 0
        efficiency_score = (productive_hours / (total_hours - idle_hours - break_hours) * 100) if (total_hours - idle_hours - break_hours) > 0 else 0
        focus_score = (productive_hours / total_hours * 100) if total_hours > 0 else 0

        # Generate recommendations
        recommendations = []
        if idle_hours > total_hours * 0.1:
            recommendations.append('Reduce idle time by staying focused on tasks')
        if break_hours > total_hours * 0.2:
            recommendations.append('Consider optimizing break patterns')
        if productivity_score < 70:
            recommendations.append('Focus on high-value tasks to improve productivity')

        # Trends (simplified)
        trends = []
        current_date = start_date
        while current_date <= end_date:
            day_entries = queryset.filter(start_time__date=current_date)
            day_hours = day_entries.aggregate(
                total=Sum(ExpressionWrapper(
                    F('duration_minutes') / 60,
                    output_field=fields.DecimalField()
                ))
            )['total'] or 0

            trends.append({
                'date': current_date.isoformat(),
                'hours': float(day_hours),
                'entries': day_entries.count()
            })

            current_date += timedelta(days=1)

        # Insights
        insights = [
            f'Average {total_hours / (end_date - start_date).days:.1f} hours per day',
            f'Productivity score: {productivity_score:.1f}%',
            f'Efficiency score: {efficiency_score:.1f}%',
            f'Idle time: {idle_hours:.1f} hours ({idle_hours / total_hours * 100:.1f}%)' if total_hours > 0 else 'No data'
        ]

        result = {
            'total_hours': float(total_hours),
            'productive_hours': float(productive_hours),
            'idle_hours': float(idle_hours),
            'break_hours': float(break_hours),
            'productivity_score': float(productivity_score),
            'efficiency_score': float(efficiency_score),
            'focus_score': float(focus_score),
            'recommendations': recommendations,
            'trends': trends,
            'insights': insights
        }

        response_serializer = TimeEntryProductivityResultSerializer(result)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_compliance(request):
    """Check compliance."""
    serializer = TimeEntryComplianceSerializer(data=request.data)

    if serializer.is_valid():
        # Simplified compliance check
        queryset = TimeEntry.objects.filter(
            organization__users=request.user
        )

        if serializer.validated_data.get('start_date'):
            queryset = queryset.filter(start_time__date__gte=serializer.validated_data['start_date'])
        if serializer.validated_data.get('end_date'):
            queryset = queryset.filter(start_time__date__lte=serializer.validated_data['end_date'])

        check_types = serializer.validated_data['check_types']

        compliance_results = []

        for check_type in check_types:
            if check_type == 'overtime':
                # Check for overtime (simplified)
                daily_hours = queryset.values('start_time__date').annotate(
                    hours=Sum(ExpressionWrapper(
                        F('duration_minutes') / 60,
                        output_field=fields.DecimalField()
                    ))
                ).filter(hours__gt=8)

                violations = []
                for day in daily_hours:
                    violations.append(f"{day['start_time__date']}: {day['hours']:.1f} hours")

                compliance_results.append({
                    'check_type': 'overtime',
                    'status': 'compliant' if not violations else 'violations_found',
                    'violations': violations,
                    'recommendations': ['Monitor daily working hours'] if violations else [],
                    'severity': 'medium' if violations else 'low',
                    'compliance_score': 90 if not violations else 70
                })

            elif check_type == 'breaks':
                # Check for adequate breaks (simplified)
                long_sessions = queryset.filter(duration_minutes__gt=360)  # 6+ hours

                violations = []
                for session in long_sessions:
                    violations.append(f"Long session: {session.duration_minutes} minutes on {session.start_time.date()}")

                compliance_results.append({
                    'check_type': 'breaks',
                    'status': 'compliant' if not violations else 'violations_found',
                    'violations': violations,
                    'recommendations': ['Take regular breaks during long sessions'] if violations else [],
                    'severity': 'low' if not violations else 'medium',
                    'compliance_score': 95 if not violations else 75
                })

            elif check_type == 'location':
                # Check location consistency (simplified)
                location_issues = queryset.filter(
                    Q(location__isnull=True) | Q(location='')
                )

                violations = []
                for entry in location_issues[:5]:  # Limit to first 5
                    violations.append(f"Missing location: {entry.start_time.date()}")

                compliance_results.append({
                    'check_type': 'location',
                    'status': 'compliant' if not violations else 'violations_found',
                    'violations': violations,
                    'recommendations': ['Ensure location is recorded for all entries'] if violations else [],
                    'severity': 'low',
                    'compliance_score': 85 if not violations else 65
                })

        response_serializer = TimeEntryComplianceResultSerializer(compliance_results, many=True)
        return Response(response_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def backup_time_entries(request):
    """Backup time entries."""
    serializer = TimeEntryBackupSerializer(data=request.data)

    if serializer.is_valid():
        # Simplified backup - would need actual backup implementation