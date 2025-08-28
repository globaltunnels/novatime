"""
Views for tasks app.

This module contains API views for managing projects, tasks, assignments,
epics, sprints, dependencies, templates, comments, attachments, tags,
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
from datetime import timedelta
from decimal import Decimal

from .models import (
    Project, Task, Assignment, Epic, Sprint, Dependency,
    Template, Comment, Attachment, Tag
)
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, TaskSerializer,
    TaskCreateSerializer, AssignmentSerializer, EpicSerializer,
    SprintSerializer, DependencySerializer, TemplateSerializer,
    CommentSerializer, AttachmentSerializer, TagSerializer,
    ProjectStatsSerializer, TaskBulkActionSerializer, ProjectTemplateSerializer,
    TaskTemplateSerializer, ProjectImportSerializer, TaskMoveSerializer,
    TaskCloneSerializer, ProjectGanttSerializer, SprintBurndownSerializer,
    ProjectTimelineSerializer, TaskTimeTrackingSerializer,
    ProjectWorkloadSerializer, ProjectRiskSerializer, ProjectQualitySerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project model."""

    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter projects by current user's access."""
        return Project.objects.filter(
            Q(workspace__memberships__user=self.request.user, workspace__memberships__is_active=True) |
            Q(assignments__user=self.request.user, assignments__is_active=True)
        ).distinct().prefetch_related('organization', 'workspace', 'owner', 'created_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        """Create project."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get project statistics."""
        project = self.get_object()

        # Get basic counts
        total_tasks = project.get_tasks_count()
        completed_tasks = project.get_completed_tasks_count()
        overdue_tasks = project.get_overdue_tasks_count()
        in_progress_tasks = project.tasks.filter(status='in_progress').count()
        todo_tasks = project.tasks.filter(status='todo').count()
        blocked_tasks = project.tasks.filter(status='blocked').count()
        total_team_members = project.get_team_members_count()
        active_team_members = project.assignments.filter(is_active=True).values('user').distinct().count()

        # Get hours data
        total_estimated_hours = project.get_total_estimated_hours()
        total_logged_hours = project.get_total_logged_hours() / 60  # Convert to hours

        # Calculate averages
        average_hours_per_task = (total_logged_hours / total_tasks) if total_tasks > 0 else 0

        # Calculate rates
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        overdue_rate = (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Budget utilization (placeholder)
        budget_utilization = project.get_budget_utilization()

        # Velocity (completed tasks per week - simplified)
        velocity = completed_tasks / max(1, (timezone.now().date() - project.created_at.date()).days / 7)

        # Burndown data (last 30 days)
        burndown_data = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            tasks_on_date = project.tasks.filter(
                Q(created_at__date__lte=date) &
                (Q(completed_at__date__gt=date) | Q(completed_at__isnull=True))
            ).count()
            burndown_data.append({
                'date': date.isoformat(),
                'remaining_tasks': tasks_on_date
            })

        # Team performance (simplified)
        team_performance = []
        for assignment in project.assignments.filter(is_active=True).distinct('user'):
            user_tasks = project.tasks.filter(assignee=assignment.user)
            completed = user_tasks.filter(status='done').count()
            total = user_tasks.count()
            completion_rate = (completed / total * 100) if total > 0 else 0

            team_performance.append({
                'user_id': str(assignment.user.id),
                'user_name': assignment.user.get_full_name(),
                'tasks_completed': completed,
                'total_tasks': total,
                'completion_rate': completion_rate
            })

        stats = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'in_progress_tasks': in_progress_tasks,
            'todo_tasks': todo_tasks,
            'blocked_tasks': blocked_tasks,
            'total_team_members': total_team_members,
            'active_team_members': active_team_members,
            'total_estimated_hours': float(total_estimated_hours),
            'total_logged_hours': float(total_logged_hours),
            'average_hours_per_task': float(average_hours_per_task),
            'completion_rate': float(completion_rate),
            'overdue_rate': float(overdue_rate),
            'budget_utilization': float(budget_utilization),
            'velocity': float(velocity),
            'burndown_data': burndown_data,
            'team_performance': team_performance
        }

        serializer = ProjectStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def gantt(self, request, pk=None):
        """Get project Gantt chart data."""
        project = self.get_object()

        # Get all tasks with dates
        tasks = project.tasks.filter(
            Q(start_date__isnull=False) | Q(due_date__isnull=False)
        ).prefetch_related('assignee', 'dependencies')

        # Build task data
        task_data = []
        for task in tasks:
            task_data.append({
                'id': str(task.id),
                'name': task.title,
                'start': task.start_date.isoformat() if task.start_date else None,
                'end': task.due_date.isoformat() if task.due_date else None,
                'progress': task.progress_percentage,
                'assignee': task.assignee.get_full_name() if task.assignee else None,
                'status': task.status,
                'priority': task.priority
            })

        # Build dependencies
        dependencies = []
        for dependency in project.dependencies.all():
            dependencies.append({
                'from': str(dependency.blocking_task.id),
                'to': str(dependency.dependent_task.id),
                'type': dependency.dependency_type
            })

        # Build milestones (completed tasks with no dependencies)
        milestones = []
        for task in project.tasks.filter(status='done'):
            if not task.dependencies.filter(dependent_task=task).exists():
                milestones.append({
                    'id': str(task.id),
                    'name': task.title,
                    'date': task.completed_at.date().isoformat() if task.completed_at else None
                })

        # Build resources (team members)
        resources = []
        for assignment in project.assignments.filter(is_active=True).distinct('user'):
            resources.append({
                'id': str(assignment.user.id),
                'name': assignment.user.get_full_name(),
                'role': assignment.role
            })

        # Build timeline
        timeline = {
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
            'current_date': timezone.now().date().isoformat()
        }

        data = {
            'tasks': task_data,
            'dependencies': dependencies,
            'milestones': milestones,
            'resources': resources,
            'timeline': timeline
        }

        serializer = ProjectGanttSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get project timeline data."""
        project = self.get_object()

        # Build phases (epics)
        phases = []
        for epic in project.epics.all():
            phases.append({
                'id': str(epic.id),
                'name': epic.name,
                'description': epic.description,
                'status': epic.status,
                'progress': epic.progress_percentage,
                'start_date': None,  # Would need to calculate from tasks
                'end_date': None
            })

        # Build milestones
        milestones = []
        for task in project.tasks.filter(status='done').order_by('completed_at'):
            milestones.append({
                'id': str(task.id),
                'name': task.title,
                'date': task.completed_at.date().isoformat() if task.completed_at else None,
                'type': 'task_completion'
            })

        # Build dependencies
        dependencies = []
        for dependency in project.dependencies.all():
            dependencies.append({
                'from': str(dependency.blocking_task.id),
                'to': str(dependency.dependent_task.id),
                'type': dependency.dependency_type,
                'lag': dependency.lag_days
            })

        # Critical path (simplified - would need proper algorithm)
        critical_path = []
        for task in project.tasks.filter(priority='highest'):
            critical_path.append(str(task.id))

        # Resource allocation (simplified)
        resource_allocation = {}
        for assignment in project.assignments.filter(is_active=True):
            user_id = str(assignment.user.id)
            if user_id not in resource_allocation:
                resource_allocation[user_id] = {
                    'name': assignment.user.get_full_name(),
                    'tasks': [],
                    'capacity': assignment.load_percentage
                }
            resource_allocation[user_id]['tasks'].append({
                'id': str(assignment.task.id) if assignment.task else None,
                'title': assignment.task.title if assignment.task else None
            })

        data = {
            'phases': phases,
            'milestones': milestones,
            'dependencies': dependencies,
            'critical_path': critical_path,
            'resource_allocation': resource_allocation
        }

        serializer = ProjectTimelineSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def workload(self, request, pk=None):
        """Get project workload data."""
        project = self.get_object()

        # Team members
        team_members = []
        for assignment in project.assignments.filter(is_active=True).distinct('user'):
            user_tasks = project.tasks.filter(assignee=assignment.user)
            estimated_hours = user_tasks.aggregate(
                total=Sum('estimated_hours')
            )['total'] or 0

            logged_hours = user_tasks.aggregate(
                total=Sum('time_entries__duration_minutes')
            )['total'] or 0
            logged_hours = logged_hours / 60 if logged_hours else 0

            team_members.append({
                'user_id': str(assignment.user.id),
                'name': assignment.user.get_full_name(),
                'role': assignment.role,
                'assigned_tasks': user_tasks.count(),
                'estimated_hours': float(estimated_hours),
                'logged_hours': float(logged_hours),
                'remaining_hours': float(estimated_hours - logged_hours),
                'capacity': assignment.load_percentage
            })

        # Task distribution
        task_distribution = {}
        for status in ['todo', 'in_progress', 'review', 'done', 'blocked']:
            count = project.tasks.filter(status=status).count()
            task_distribution[status] = count

        # Capacity utilization
        capacity_utilization = {}
        for member in team_members:
            utilization = (member['logged_hours'] / (member['capacity'] * 40 / 100)) * 100 if member['capacity'] > 0 else 0
            capacity_utilization[member['user_id']] = min(100, utilization)

        # Workload trend (last 4 weeks)
        workload_trend = []
        for i in range(4):
            week_start = timezone.now().date() - timedelta(days=(i + 1) * 7)
            week_end = week_start + timedelta(days=6)
            week_entries = project.time_entries.filter(
                start_time__date__gte=week_start,
                start_time__date__lte=week_end
            )
            week_hours = week_entries.aggregate(
                total=Sum(ExpressionWrapper(
                    F('duration_minutes') / 60,
                    output_field=fields.DecimalField()
                ))
            )['total'] or 0
            workload_trend.append({
                'week': f'Week {4-i}',
                'hours': float(week_hours)
            })

        # Bottlenecks (simplified)
        bottlenecks = []
        overdue_count = project.get_overdue_tasks_count()
        if overdue_count > 0:
            bottlenecks.append({
                'type': 'overdue_tasks',
                'count': overdue_count,
                'severity': 'high'
            })

        blocked_count = project.tasks.filter(status='blocked').count()
        if blocked_count > 0:
            bottlenecks.append({
                'type': 'blocked_tasks',
                'count': blocked_count,
                'severity': 'medium'
            })

        # Recommendations (simplified)
        recommendations = []
        if overdue_count > 0:
            recommendations.append('Address overdue tasks to prevent schedule slippage')
        if blocked_count > 0:
            recommendations.append('Resolve task dependencies to unblock progress')

        data = {
            'team_members': team_members,
            'task_distribution': task_distribution,
            'capacity_utilization': capacity_utilization,
            'workload_trend': workload_trend,
            'bottlenecks': bottlenecks,
            'recommendations': recommendations
        }

        serializer = ProjectWorkloadSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def risk(self, request, pk=None):
        """Get project risk assessment."""
        project = self.get_object()

        # Risk factors
        risk_factors = []

        # Schedule risk
        overdue_tasks = project.get_overdue_tasks_count()
        if overdue_tasks > 0:
            risk_factors.append({
                'type': 'schedule',
                'description': f'{overdue_tasks} tasks are overdue',
                'impact': 'high',
                'probability': 'high'
            })

        # Scope risk
        blocked_tasks = project.tasks.filter(status='blocked').count()
        if blocked_tasks > 0:
            risk_factors.append({
                'type': 'scope',
                'description': f'{blocked_tasks} tasks are blocked',
                'impact': 'medium',
                'probability': 'medium'
            })

        # Resource risk
        total_members = project.get_team_members_count()
        if total_members == 0:
            risk_factors.append({
                'type': 'resource',
                'description': 'No team members assigned',
                'impact': 'high',
                'probability': 'high'
            })

        # Budget risk
        budget_utilization = project.get_budget_utilization()
        if budget_utilization > 90:
            risk_factors.append({
                'type': 'budget',
                'description': f'Budget utilization at {budget_utilization}%',
                'impact': 'high',
                'probability': 'medium'
            })

        # Calculate overall risk score
        risk_score = 0
        for factor in risk_factors:
            impact_score = {'low': 1, 'medium': 2, 'high': 3}[factor['impact']]
            prob_score = {'low': 1, 'medium': 2, 'high': 3}[factor['probability']]
            risk_score += impact_score * prob_score

        # Determine risk level
        if risk_score >= 15:
            risk_level = 'critical'
        elif risk_score >= 10:
            risk_level = 'high'
        elif risk_score >= 5:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        # Mitigation strategies
        mitigation_strategies = []
        if overdue_tasks > 0:
            mitigation_strategies.append('Reassign overdue tasks to available team members')
        if blocked_tasks > 0:
            mitigation_strategies.append('Resolve task dependencies and blockers')
        if total_members == 0:
            mitigation_strategies.append('Assign team members to the project')

        # Contingency plans
        contingency_plans = [
            'Regular status meetings to identify issues early',
            'Maintain a buffer in the project schedule',
            'Cross-train team members for critical tasks',
            'Have a rollback plan for major changes'
        ]

        # Risk trend (simplified)
        risk_trend = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            # Would need historical data for real trend
            risk_trend.append({
                'date': date.isoformat(),
                'score': risk_score
            })

        data = {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'mitigation_strategies': mitigation_strategies,
            'contingency_plans': contingency_plans,
            'risk_score': risk_score,
            'risk_trend': risk_trend
        }

        serializer = ProjectRiskSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the project."""
        project = self.get_object()
        serializer = AssignmentSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Check permissions
            user_membership = project.workspace.memberships.get(user=request.user)
            if user_membership.role not in ['owner', 'admin']:
                return Response(
                    {'error': _('You don\'t have permission to manage project members.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            assignment, created = serializer.save()
            response_serializer = AssignmentSerializer(assignment)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the project."""
        project = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': _('User ID is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions
        user_membership = project.workspace.memberships.get(user=request.user)
        if user_membership.role not in ['owner', 'admin']:
            return Response(
                {'error': _('You don\'t have permission to manage project members.')},
                status=status.HTTP_403_FORBIDDEN
            )

        result = project.remove_member(user_id)
        if result:
            return Response({'message': _('Member removed successfully.')})
        else:
            return Response(
                {'error': _('User is not a member of this project.')},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def create_template(self, request, pk=None):
        """Create a template from this project."""
        project = self.get_object()
        serializer = ProjectTemplateSerializer(data=request.data)

        if serializer.is_valid():
            # Check permissions
            if project.owner != request.user:
                return Response(
                    {'error': _('Only project owner can create templates.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Build template data
            template_data = {
                'name': serializer.validated_data['name'],
                'description': serializer.validated_data.get('description', ''),
                'project_type': project.project_type,
                'methodology': project.methodology,
                'tasks': [],
                'epics': [],
                'sprints': [],
                'dependencies': [],
                'assignments': []
            }

            if serializer.validated_data['include_tasks']:
                for task in project.tasks.all():
                    task_data = {
                        'title': task.title,
                        'description': task.description,
                        'status': 'todo',  # Reset status
                        'priority': task.priority,
                        'estimated_hours': task.estimated_hours,
                        'labels': task.labels,
                        'custom_fields': task.custom_fields
                    }
                    template_data['tasks'].append(task_data)

            if serializer.validated_data['include_epics']:
                for epic in project.epics.all():
                    epic_data = {
                        'name': epic.name,
                        'description': epic.description,
                        'priority': epic.priority
                    }
                    template_data['epics'].append(epic_data)

            if serializer.validated_data['include_sprints']:
                for sprint in project.sprints.all():
                    sprint_data = {
                        'name': sprint.name,
                        'goal': sprint.goal,
                        'planned_capacity': sprint.planned_capacity
                    }
                    template_data['sprints'].append(sprint_data)

            if serializer.validated_data['include_dependencies']:
                for dependency in project.dependencies.all():
                    dependency_data = {
                        'blocking_task_index': None,  # Would need to map to template tasks
                        'dependent_task_index': None,
                        'dependency_type': dependency.dependency_type,
                        'lag_days': dependency.lag_days
                    }
                    template_data['dependencies'].append(dependency_data)

            if serializer.validated_data['include_assignments']:
                for assignment in project.assignments.all():
                    assignment_data = {
                        'role': assignment.role,
                        'load_percentage': assignment.load_percentage
                    }
                    template_data['assignments'].append(assignment_data)

            # Create template
            template = Template.objects.create(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                template_type='project',
                template_data=template_data,
                organization=project.organization,
                created_by=request.user
            )

            response_serializer = TemplateSerializer(template)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def import_from_template(self, request):
        """Import project from template."""
        serializer = ProjectImportSerializer(data=request.data)

        if serializer.is_valid():
            template_id = serializer.validated_data['template_id']
            name = serializer.validated_data['name']
            workspace_id = serializer.validated_data['workspace_id']

            # Get template
            try:
                template = Template.objects.get(id=template_id, template_type='project')
            except Template.DoesNotExist:
                return Response(
                    {'error': _('Template not found.')},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get workspace
            try:
                workspace = Workspace.objects.get(id=workspace_id)
                if not workspace.can_user_access(request.user):
                    return Response(
                        {'error': _('You don\'t have access to this workspace.')},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Workspace.DoesNotExist:
                return Response(
                    {'error': _('Workspace not found.')},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create project from template
            with transaction.atomic():
                project = Project.objects.create(
                    name=name,
                    description=template.template_data.get('description', ''),
                    project_type=template.template_data.get('project_type', 'software'),
                    methodology=template.template_data.get('methodology', 'agile'),
                    organization=workspace.organization,
                    workspace=workspace,
                    created_by=request.user,
                    owner=request.user
                )

                # Import tasks
                task_mapping = {}
                for i, task_data in enumerate(template.template_data.get('tasks', [])):
                    task = Task.objects.create(
                        project=project,
                        title=task_data['title'],
                        description=task_data.get('description', ''),
                        priority=task_data.get('priority', 'medium'),
                        estimated_hours=task_data.get('estimated_hours', 0),
                        labels=task_data.get('labels', []),
                        custom_fields=task_data.get('custom_fields', {}),
                        created_by=request.user
                    )
                    task_mapping[i] = task

                # Import epics
                for epic_data in template.template_data.get('epics', []):
                    Epic.objects.create(
                        project=project,
                        name=epic_data['name'],
                        description=epic_data.get('description', ''),
                        priority=epic_data.get('priority', 'medium'),
                        created_by=request.user
                    )

                # Import sprints
                for sprint_data in template.template_data.get('sprints', []):
                    Sprint.objects.create(
                        project=project,
                        name=sprint_data['name'],
                        goal=sprint_data.get('goal', ''),
                        planned_capacity=sprint_data.get('planned_capacity', 0),
                        created_by=request.user
                    )

                # Increment template usage
                template.increment_usage()

            response_serializer = ProjectSerializer(project)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task model."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tasks by current user's access."""
        return Task.objects.filter(
            Q(project__workspace__memberships__user=self.request.user, project__workspace__memberships__is_active=True) |
            Q(project__assignments__user=self.request.user, project__assignments__is_active=True) |
            Q(assignee=self.request.user)
        ).distinct().prefetch_related('project', 'assignee', 'reporter', 'epic', 'sprint')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        """Create task."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def time_tracking(self, request, pk=None):
        """Get task time tracking data."""
        task = self.get_object()

        # Get time entries
        time_entries = task.time_entries.all().order_by('-start_time')

        # Calculate metrics
        logged_hours = task.get_logged_hours() / 60
        estimated_hours = task.estimated_hours
        remaining_hours = max(0, estimated_hours - logged_hours)

        # Build time entries data
        entries_data = []
        for entry in time_entries:
            entries_data.append({
                'id': str(entry.id),
                'start_time': entry.start_time.isoformat(),
                'end_time': entry.end_time.isoformat() if entry.end_time else None,
                'duration_minutes': entry.duration_minutes,
                'description': entry.description,
                'user': entry.user.get_full_name(),
                'entry_type': entry.entry_type
            })

        # Calculate efficiency (simplified)
        efficiency = (logged_hours / estimated_hours * 100) if estimated_hours > 0 else 0

        # Productivity trend (last 7 days)
        productivity_trend = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            day_entries = task.time_entries.filter(start_time__date=date)
            day_hours = day_entries.aggregate(
                total=Sum(ExpressionWrapper(
                    F('duration_minutes') / 60,
                    output_field=fields.DecimalField()
                ))
            )['total'] or 0
            productivity_trend.append({
                'date': date.isoformat(),
                'hours': float(day_hours)
            })

        data = {
            'task_id': str(task.id),
            'logged_hours': float(logged_hours),
            'estimated_hours': float(estimated_hours),
            'remaining_hours': float(remaining_hours),
            'time_entries': entries_data,
            'efficiency': float(efficiency),
            'productivity_trend': productivity_trend
        }

        serializer = TaskTimeTrackingSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on tasks."""
        serializer = TaskBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            task_ids = serializer.validated_data['task_ids']
            action = serializer.validated_data['action']

            tasks = Task.objects.filter(
                id__in=task_ids,
                project__workspace__memberships__user=request.user,
                project__workspace__memberships__is_active=True
            )

            updated_count = 0
            for task in tasks:
                # Check permissions
                if not task.can_user_edit(request.user):
                    continue

                if action == 'update_status':
                    task.status = serializer.validated_data['status']
                elif action == 'update_priority':
                    task.priority = serializer.validated_data['priority']
                elif action == 'update_assignee':
                    task.assignee_id = serializer.validated_data['assignee_id']
                elif action == 'update_due_date':
                    task.due_date = serializer.validated_data['due_date']
                elif action == 'add_labels':
                    labels = serializer.validated_data['labels']
                    task.labels = list(set(task.labels + labels))
                elif action == 'remove_labels':
                    labels = serializer.validated_data['labels']
                    task.labels = [l for l in task.labels if l not in labels]
                elif action == 'delete':
                    task.delete()
                    continue

                task.save()
                updated_count += 1

            return Response({
                'message': _('Bulk action completed successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def move_tasks(self, request):
        """Move tasks between projects/epics/sprints."""
        serializer = TaskMoveSerializer(data=request.data)

        if serializer.is_valid():
            task_ids = serializer.validated_data['task_ids']
            project_id = serializer.validated_data.get('project_id')
            epic_id = serializer.validated_data.get('epic_id')
            sprint_id = serializer.validated_data.get('sprint_id')

            tasks = Task.objects.filter(
                id__in=task_ids,
                project__workspace__memberships__user=request.user,
                project__workspace__memberships__is_active=True
            )

            updated_count = 0
            for task in tasks:
                # Check permissions
                if not task.can_user_edit(request.user):
                    continue

                if project_id:
                    try:
                        new_project = Project.objects.get(id=project_id)
                        if new_project.can_user_access(request.user):
                            task.project = new_project
                    except Project.DoesNotExist:
                        continue

                if epic_id:
                    try:
                        new_epic = Epic.objects.get(id=epic_id, project=task.project)
                        task.epic = new_epic
                    except Epic.DoesNotExist:
                        continue

                if sprint_id:
                    try:
                        new_sprint = Sprint.objects.get(id=sprint_id, project=task.project)
                        task.sprint = new_sprint
                    except Sprint.DoesNotExist:
                        continue

                task.save()
                updated_count += 1

            return Response({
                'message': _('Tasks moved successfully.'),
                'updated_count': updated_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def clone_tasks(self, request):
        """Clone tasks."""
        serializer = TaskCloneSerializer(data=request.data)

        if serializer.is_valid():
            task_ids = serializer.validated_data['task_ids']
            project_id = serializer.validated_data.get('project_id')
            include_subtasks = serializer.validated_data['include_subtasks']
            include_comments = serializer.validated_data['include_comments']
            include_attachments = serializer.validated_data['include_attachments']
            include_dependencies = serializer.validated_data['include_dependencies']

            tasks = Task.objects.filter(
                id__in=task_ids,
                project__workspace__memberships__user=request.user,
                project__workspace__memberships__is_active=True
            )

            cloned_tasks = []
            for task in tasks:
                # Check permissions
                if not task.can_user_edit(request.user):
                    continue

                # Determine target project
                target_project = task.project
                if project_id:
                    try:
                        target_project = Project.objects.get(id=project_id)
                        if not target_project.can_user_access(request.user):
                            continue
                    except Project.DoesNotExist:
                        continue

                # Clone task
                cloned_task = Task.objects.create(
                    project=target_project,
                    title=f"[Clone] {task.title}",
                    description=task.description,
                    priority=task.priority,
                    estimated_hours=task.estimated_hours,
                    labels=task.labels,
                    custom_fields=task.custom_fields,
                    created_by=request.user
                )

                # Clone subtasks
                if include_subtasks:
                    for subtask in task.subtasks.all():
                        Task.objects.create(
                            project=target_project,
                            parent_task=cloned_task,
                            title=subtask.title,
                            description=subtask.description,
                            priority=subtask.priority,
                            estimated_hours=subtask.estimated_hours,
                            labels=subtask.labels,
                            custom_fields=subtask.custom_fields,
                            created_by=request.user
                        )

                # Clone comments
                if include_comments:
                    for comment in task.comments.all():
                        Comment.objects.create(
                            task=cloned_task,
                            author=request.user,
                            content=comment.content,
                            parent_comment=None  # Don't clone threading
                        )

                # Clone attachments (would need file copying logic)
                if include_attachments:
                    pass  # Placeholder for attachment cloning

                # Clone dependencies (would need task mapping)
                if include_dependencies:
                    pass  # Placeholder for dependency cloning

                cloned_tasks.append(cloned_task)

            response_serializer = TaskSerializer(cloned_tasks, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_template(self, request, pk=None):
        """Create a template from this task."""
        task = self.get_object()
        serializer = TaskTemplateSerializer(data=request.data)

        if serializer.is_valid():
            # Check permissions
            if not task.can_user_edit(request.user):
                return Response(
                    {'error': _('You don\'t have permission to create templates from this task.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Build template data
            template_data = {
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'estimated_hours': task.estimated_hours,
                'labels': task.labels,
                'custom_fields': task.custom_fields,
                'subtasks': [],
                'comments': [],
                'attachments': [],
                'dependencies': []
            }

            if serializer.validated_data['include_subtasks']:
                for subtask in task.subtasks.all():
                    subtask_data = {
                        'title': subtask.title,
                        'description': subtask.description,
                        'priority': subtask.priority,
                        'estimated_hours': subtask.estimated_hours,
                        'labels': subtask.labels,
                        'custom_fields': subtask.custom_fields
                    }
                    template_data['subtasks'].append(subtask_data)

            if serializer.validated_data['include_comments']:
                for comment in task.comments.all():
                    comment_data = {
                        'content': comment.content
                    }
                    template_data['comments'].append(comment_data)

            if serializer.validated_data['include_attachments']:
                for attachment in task.attachments.all():
                    attachment_data = {
                        'filename': attachment.filename,
                        'content_type': attachment.content_type
                    }
                    template_data['attachments'].append(attachment_data)

            if serializer.validated_data['include_dependencies']:
                for dependency in task.blocking_dependencies.all():
                    dependency_data = {
                        'blocking_task_title': dependency.blocking_task.title,
                        'dependency_type': dependency.dependency_type,
                        'lag_days': dependency.lag_days
                    }
                    template_data['dependencies'].append(dependency_data)

            # Create template
            template = Template.objects.create(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                template_type='task',
                template_data=template_data,
                organization=task.project.organization,
                created_by=request.user
            )

            response_serializer = TemplateSerializer(template)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Assignment model."""

    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter assignments by current user's projects."""
        return Assignment.objects.filter(
            project__workspace__memberships__user=self.request.user,
            project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('project', 'user', 'task')


class EpicViewSet(viewsets.ModelViewSet):
    """ViewSet for Epic model."""

    serializer_class = EpicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter epics by current user's projects."""
        return Epic.objects.filter(
            project__workspace__memberships__user=self.request.user,
            project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('project', 'created_by')


class SprintViewSet(viewsets.ModelViewSet):
    """ViewSet for Sprint model."""

    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter sprints by current user's projects."""
        return Sprint.objects.filter(
            project__workspace__memberships__user=self.request.user,
            project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('project', 'created_by')

    @action(detail=True, methods=['get'])
    def burndown(self, request, pk=None):
        """Get sprint burndown chart data."""
        sprint = self.get_object()

        # Get sprint tasks
        tasks = sprint.tasks.all()

        # Calculate total story points (using estimated hours as proxy)
        total_points = tasks.aggregate(
            total=Sum('estimated_hours')
        )['total'] or 0

        # Build burndown data
        dates = []
        ideal_burndown = []
        actual_burndown = []
        scope_changes = []
        completed_tasks = []

        sprint_days = (sprint.end_date - sprint.start_date).days + 1
        for i in range(sprint_days):
            date = sprint.start_date + timedelta(days=i)
            dates.append(date.isoformat())

            # Ideal burndown (linear)
            days_remaining = sprint_days - i - 1
            ideal_remaining = (total_points * days_remaining) / sprint_days
            ideal_burndown.append(float(ideal_remaining))

            # Actual burndown
            completed_on_date = tasks.filter(
                completed_at__date__lte=date,
                status='done'
            ).aggregate(
                total=Sum('estimated_hours')
            )['total'] or 0
            actual_burndown.append(float(total_points - completed_on_date))

            # Completed tasks on this date
            day_completed = tasks.filter(
                completed_at__date=date,
                status='done'
            )
            completed_tasks.append(day_completed.count())

        # Scope changes (simplified - tasks added/removed during sprint)
        scope_changes = [0] * sprint_days  # Placeholder

        data = {
            'dates': dates,
            'ideal_burndown': ideal_burndown,
            'actual_burndown': actual_burndown,
            'scope_changes': scope_changes,
            'completed_tasks': completed_tasks
        }

        serializer = SprintBurndownSerializer(data)
        return Response(serializer.data)


class DependencyViewSet(viewsets.ModelViewSet):
    """ViewSet for Dependency model."""

    serializer_class = DependencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter dependencies by current user's projects."""
        return Dependency.objects.filter(
            project__workspace__memberships__user=self.request.user,
            project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('project', 'blocking_task', 'dependent_task')


class TemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for Template model."""

    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter templates by current user's organizations or public templates."""
        return Template.objects.filter(
            Q(organization__users=self.request.user) |
            Q(is_public=True)
        ).distinct().prefetch_related('organization', 'created_by')


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment model."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter comments by current user's tasks."""
        return Comment.objects.filter(
            task__project__workspace__memberships__user=self.request.user,
            task__project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('task', 'author', 'parent_comment')


class AttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Attachment model."""

    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter attachments by current user's tasks."""
        return Attachment.objects.filter(
            task__project__workspace__memberships__user=self.request.user,
            task__project__workspace__memberships__is_active=True
        ).distinct().prefetch_related('task', 'uploaded_by')


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag model."""

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter tags by current user's organizations."""
        return Tag.objects.filter(
            organization__users=self.request.user
        ).distinct().prefetch_related('organization', 'created_by')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_quality(request, project_id):
    """Get project quality metrics."""
    try:
        project = Project.objects.get(
            id=project_id,
            workspace__memberships__user=request.user,
            workspace__memberships__is_active=True
        )

        # Quality metrics (simplified placeholders)
        code_quality_score = 85.5
        test_coverage = 78.2
        defect_density = 2.1
        technical_debt = 15.3
        maintainability_index = 72.8

        # Quality trend (simplified)
        quality_trend = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            quality_trend.append({
                'date': date.isoformat(),
                'score': code_quality_score - i
            })

        # Recommendations
        recommendations = [
            'Increase test coverage to above 80%',
            'Address technical debt in legacy modules',
            'Implement code quality gates in CI/CD',
            'Regular code review practices'
        ]

        data = {
            'code_quality_score': code_quality_score,
            'test_coverage': test_coverage,
            'defect_density': defect_density,
            'technical_debt': technical_debt,
            'maintainability_index': maintainability_index,
            'quality_trend': quality_trend,
            'recommendations': recommendations
        }

        serializer = ProjectQualitySerializer(data)
        return Response(serializer.data)

    except Project.DoesNotExist:
        return Response(
            {'error': _('Project not found.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_task_suggestions(request, project_id):
    """Get AI-powered task suggestions."""
    try:
        project = Project.objects.get(
            id=project_id,
            workspace__memberships__user=request.user,
            workspace__memberships__is_active=True
        )

        # AI suggestions (placeholder - would integrate with AI service)
        suggestions = [
            {
                'type': 'missing_dependencies',
                'description': 'Task "Implement user authentication" is missing dependency on "Design database schema"',
                'confidence': 0.85,
                'action': 'add_dependency'
            },
            {
                'type': 'overestimated_effort',
                'description': 'Task "Create user interface mockups" may be overestimated by 2-3 hours',
                'confidence': 0.72,
                'action': 'adjust_estimate'
            },
            {
                'type': 'resource_conflict',
                'description': 'John Smith is overloaded with 5 high-priority tasks this sprint',
                'confidence': 0.91,
                'action': 'reassign_tasks'
            }
        ]

        return Response({
            'project_id': str(project.id),
            'suggestions': suggestions,
            'generated_at': timezone.now().isoformat()
        })

    except Project.DoesNotExist:
        return Response(
            {'error': _('Project not found.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_assignments(request, project_id):
    """Optimize task assignments using AI."""
    try:
        project = Project.objects.get(
            id=project_id,
            workspace__memberships__user=request.user,
            workspace__memberships__is_active=True
        )

        # AI optimization (placeholder - would integrate with AI service)
        optimizations = [
            {
                'task_id': 'task-123',
                'task_title': 'Implement payment processing',
                'current_assignee': 'John Smith',
                'recommended_assignee': 'Sarah Johnson',
                'reason': 'Sarah has experience with payment systems and is currently underutilized',
                'confidence': 0.88
            },
            {
                'task_id': 'task-456',
                'task_title': 'Design user interface',
                'current_assignee': 'Mike Davis',
                'recommended_assignee': 'Mike Davis',
                'reason': 'Mike is the most qualified designer and has capacity',
                'confidence': 0.95
            }
        ]

        return Response({
            'project_id': str(project.id),
            'optimizations': optimizations,
            'optimization_score': 87.5,
            'generated_at': timezone.now().isoformat()
        })

    except Project.DoesNotExist:
        return Response(
            {'error': _('Project not found.')},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_predictive_analytics(request, project_id):
    """Get predictive analytics for project."""
    try:
        project = Project.objects.get(
            id=project_id,
            workspace__members