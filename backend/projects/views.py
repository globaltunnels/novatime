from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg
from decimal import Decimal
from datetime import datetime, timedelta

from .models import Client, Project, ProjectMember, Epic
from .serializers import (
    ClientSerializer, ProjectSerializer, ProjectCreateSerializer,
    ProjectSummarySerializer, ProjectMemberSerializer, ProjectTimelineSerializer,
    ProjectMemberActionSerializer, ProjectStatsSerializer
)
from organizations.models import Workspace
from iam.models import User


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clients.
    """
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter clients based on user's organization."""
        user = self.request.user
        # Get user's workspaces and their organizations
        workspace_ids = user.memberships.values_list('workspace_id', flat=True)
        org_ids = Workspace.objects.filter(id__in=workspace_ids).values_list('organization_id', flat=True)
        
        return Client.objects.filter(
            organization_id__in=org_ids
        ).prefetch_related('projects')
    
    def perform_create(self, serializer):
        """Set organization when creating client."""
        workspace_id = self.request.data.get('workspace')
        if workspace_id:
            workspace = Workspace.objects.get(id=workspace_id)
            serializer.save(organization=workspace.organization)
        else:
            # Default to first organization user has access to
            workspace = self.request.user.memberships.first().workspace
            serializer.save(organization=workspace.organization)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects with comprehensive CRUD operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action == 'list':
            return ProjectSummarySerializer
        elif self.action == 'timeline':
            return ProjectTimelineSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        """Filter projects based on user permissions."""
        user = self.request.user
        
        # Get projects from workspaces user has access to
        workspace_ids = user.memberships.values_list('workspace_id', flat=True)
        
        queryset = Project.objects.filter(
            workspace_id__in=workspace_ids
        ).select_related(
            'client', 'manager', 'workspace'
        ).prefetch_related(
            'members__user'
        )
        
        # Filter by workspace if specified
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by manager
        manager_id = self.request.query_params.get('manager')
        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set workspace when creating project."""
        workspace_id = self.request.data.get('workspace')
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            # Verify user has access to workspace
            user_workspaces = self.request.user.memberships.values_list('workspace_id', flat=True)
            if workspace.id not in user_workspaces:
                raise PermissionError("Access denied to this workspace")
            
            serializer.save(workspace=workspace)
        except Workspace.DoesNotExist:
            raise serializers.ValidationError("Invalid workspace")
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get project timeline view."""
        project = self.get_object()
        serializer = ProjectTimelineSerializer(project, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get project statistics and analytics."""
        project = self.get_object()
        
        # Calculate statistics
        from time_entries.models import TimeEntry
        
        time_entries = TimeEntry.objects.filter(project=project)
        
        total_minutes = time_entries.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        billable_minutes = time_entries.filter(is_billable=True).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        total_hours = Decimal(str(total_minutes / 60)) if total_minutes else Decimal('0.00')
        billable_hours = Decimal(str(billable_minutes / 60)) if billable_minutes else Decimal('0.00')
        
        # Calculate total cost
        total_cost = Decimal('0.00')
        for entry in time_entries.filter(duration_minutes__isnull=False).select_related('user'):
            hours = Decimal(str(entry.duration_minutes / 60))
            rate = entry.hourly_rate or project.hourly_rate or Decimal('0.00')
            total_cost += hours * rate
        
        # Calculate budget utilization
        budget_utilization = Decimal('0.00')
        if project.budget_hours:
            budget_utilization = (total_hours / project.budget_hours) * 100
        
        # Calculate task completion rate
        from tasks.models import Task
        tasks = Task.objects.filter(project=project)
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        task_completion_rate = Decimal('0.00')
        if total_tasks > 0:
            task_completion_rate = (Decimal(str(completed_tasks)) / Decimal(str(total_tasks))) * 100
        
        stats_data = {
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'total_cost': total_cost,
            'budget_utilization': budget_utilization,
            'task_completion_rate': task_completion_rate
        }
        
        serializer = ProjectStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a team member to the project."""
        project = self.get_object()
        serializer = ProjectMemberActionSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            
            try:
                user = User.objects.get(id=user_id)
                
                # Check if user is already a member
                if ProjectMember.objects.filter(project=project, user=user).exists():
                    return Response(
                        {'error': 'User is already a project member'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create membership
                member = ProjectMember.objects.create(
                    project=project,
                    user=user,
                    role=serializer.validated_data.get('role', 'member'),
                    hourly_rate=serializer.validated_data.get('hourly_rate'),
                    allocation_percent=serializer.validated_data.get('allocation_percent', 100)
                )
                
                member_serializer = ProjectMemberSerializer(member)
                return Response(member_serializer.data, status=status.HTTP_201_CREATED)
                
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a team member from the project."""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
            member.delete()
            return Response({'message': 'Member removed successfully'})
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['patch'])
    def update_member(self, request, pk=None):
        """Update a team member's role or settings."""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            member = ProjectMember.objects.get(project=project, user_id=user_id)
            serializer = ProjectMemberActionSerializer(data=request.data, partial=True)
            
            if serializer.is_valid():
                if 'role' in serializer.validated_data:
                    member.role = serializer.validated_data['role']
                if 'hourly_rate' in serializer.validated_data:
                    member.hourly_rate = serializer.validated_data['hourly_rate']
                if 'allocation_percent' in serializer.validated_data:
                    member.allocation_percent = serializer.validated_data['allocation_percent']
                
                member.save()
                
                member_serializer = ProjectMemberSerializer(member)
                return Response(member_serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a project as a template."""
        project = self.get_object()
        
        # Create a copy of the project
        new_project = Project.objects.create(
            workspace=project.workspace,
            name=f"{project.name} (Copy)",
            description=project.description,
            color=project.color,
            status='planning',
            billing_type=project.billing_type,
            hourly_rate=project.hourly_rate,
            fixed_price=project.fixed_price,
            budget_hours=project.budget_hours,
            require_time_entry_notes=project.require_time_entry_notes,
            track_expenses=project.track_expenses,
            manager=request.user  # Set current user as manager
        )
        
        # Copy team members if requested
        if request.data.get('copy_team', False):
            for member in project.members.all():
                ProjectMember.objects.create(
                    project=new_project,
                    user=member.user,
                    role=member.role,
                    hourly_rate=member.hourly_rate,
                    allocation_percent=member.allocation_percent
                )
        
        # Copy tasks if requested
        if request.data.get('copy_tasks', False):
            from tasks.models import Task
            for task in project.tasks.all():
                Task.objects.create(
                    project=new_project,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status='todo',  # Reset status
                    estimated_hours=task.estimated_hours
                )
        
        serializer = ProjectSerializer(new_project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get project dashboard data for current user."""
        user = request.user
        workspace_id = request.query_params.get('workspace')
        
        # Base queryset
        queryset = self.get_queryset()
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        # Get user's projects (where they are members or managers)
        user_projects = queryset.filter(
            Q(members__user=user) | Q(manager=user)
        ).distinct()
        
        # Calculate statistics
        total_projects = user_projects.count()
        active_projects = user_projects.filter(status='active').count()
        overdue_projects = user_projects.filter(
            end_date__lt=timezone.now().date(),
            status__in=['planning', 'active', 'on_hold']
        ).count()
        
        # Recent projects
        recent_projects = user_projects.order_by('-updated_at')[:5]
        
        # Projects by status
        status_breakdown = {}
        for status_choice in Project.STATUS_CHOICES:
            status_key = status_choice[0]
            status_breakdown[status_key] = user_projects.filter(status=status_key).count()
        
        dashboard_data = {
            'summary': {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'overdue_projects': overdue_projects
            },
            'status_breakdown': status_breakdown,
            'recent_projects': ProjectSummarySerializer(recent_projects, many=True).data
        }
        
        return Response(dashboard_data)


class ProjectMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing project team members.
    """
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter members based on user's project access."""
        user = self.request.user
        workspace_ids = user.memberships.values_list('workspace_id', flat=True)
        
        return ProjectMember.objects.filter(
            project__workspace_id__in=workspace_ids
        ).select_related('user', 'project').order_by('joined_at')


class ProjectReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for project reports and analytics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get project summary report."""
        workspace_id = request.query_params.get('workspace')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not workspace_id:
            return Response(
                {'error': 'workspace parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Base filter
        projects = Project.objects.filter(workspace_id=workspace_id)
        
        # Date filtering
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                projects = projects.filter(
                    Q(start_date__range=[start_date, end_date]) |
                    Q(end_date__range=[start_date, end_date])
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calculate metrics
        total_projects = projects.count()
        
        # Status distribution
        status_dist = {}
        for status_choice in Project.STATUS_CHOICES:
            status_key = status_choice[0]
            status_dist[status_key] = projects.filter(status=status_key).count()
        
        # Billing type distribution
        billing_dist = {}
        for billing_choice in Project.BILLING_TYPES:
            billing_key = billing_choice[0]
            billing_dist[billing_key] = projects.filter(billing_type=billing_key).count()
        
        # Calculate total budget and hours
        total_budget = projects.aggregate(
            total_fixed=Sum('fixed_price'),
            total_budget_hours=Sum('budget_hours')
        )
        
        report_data = {
            'period': {
                'start_date': start_date if start_date else None,
                'end_date': end_date if end_date else None
            },
            'summary': {
                'total_projects': total_projects,
                'total_budget_value': total_budget['total_fixed'] or 0,
                'total_budget_hours': total_budget['total_budget_hours'] or 0
            },
            'status_distribution': status_dist,
            'billing_distribution': billing_dist
        }
        
        return Response(report_data)