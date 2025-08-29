from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from .models import (
    AIModel, AIJob, SmartTimesheetSuggestion, 
    TaskAssignmentRecommendation, AIInsight
)
from .serializers import (
    AIModelSerializer, AIJobSerializer, SmartTimesheetSuggestionSerializer,
    TimesheetSuggestionActionSerializer, TaskAssignmentRecommendationSerializer,
    TaskAssignmentActionSerializer, AIInsightSerializer, InsightAcknowledgeSerializer,
    AIJobCreateSerializer
)
from .services import SmartTimesheetService, TaskAssignmentService, AIInsightService
from tasks.models import Task
from organizations.models import Workspace
from time_entries.models import TimeEntry


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI models."""
    
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get available AI models."""
        return AIModel.objects.filter(status='active')


class AIJobViewSet(viewsets.ModelViewSet):
    """ViewSet for AI processing jobs."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AIJobCreateSerializer
        return AIJobSerializer
    
    def get_queryset(self):
        """Filter jobs based on user permissions."""
        user = self.request.user
        workspace_id = self.request.query_params.get('workspace')
        
        queryset = AIJob.objects.filter(user=user)
        
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending or processing job."""
        job = self.get_object()
        
        if job.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Only pending or processing jobs can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'cancelled'
        job.save()
        
        return Response({'message': 'Job cancelled successfully'})


class SmartTimesheetSuggestionViewSet(viewsets.ModelViewSet):
    """ViewSet for timesheet suggestions."""
    
    serializer_class = SmartTimesheetSuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter suggestions based on user permissions."""
        user = self.request.user
        workspace_id = self.request.query_params.get('workspace')
        date_str = self.request.query_params.get('date')
        
        queryset = SmartTimesheetSuggestion.objects.filter(user=user)
        
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date)
            except ValueError:
                pass
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_for_date(self, request):
        """Generate suggestions for a specific date."""
        workspace_id = request.data.get('workspace')
        date_str = request.data.get('date')
        
        if not workspace_id or not date_str:
            return Response(
                {'error': 'workspace and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (Workspace.DoesNotExist, ValueError):
            return Response(
                {'error': 'Invalid workspace or date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate suggestions
        service = SmartTimesheetService()
        suggestions = service.generate_suggestions_for_user(
            user=request.user,
            workspace=workspace,
            date=date
        )
        
        serializer = SmartTimesheetSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a timesheet suggestion."""
        suggestion = self.get_object()
        
        if suggestion.status != 'pending':
            return Response(
                {'error': 'Only pending suggestions can be responded to'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TimesheetSuggestionActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            feedback = serializer.validated_data.get('feedback', '')
            
            suggestion.status = action
            suggestion.user_feedback = feedback
            suggestion.responded_at = timezone.now()
            
            if action == 'accept':
                # Create time entry from suggestion
                time_entry = TimeEntry.objects.create(
                    user=suggestion.user,
                    workspace=suggestion.workspace,
                    project=suggestion.project,
                    task=suggestion.task,
                    start_time=timezone.make_aware(
                        datetime.combine(suggestion.date, suggestion.suggested_start_time)
                    ),
                    end_time=timezone.make_aware(
                        datetime.combine(suggestion.date, suggestion.suggested_end_time)
                    ),
                    duration_minutes=suggestion.suggested_duration_minutes,
                    description=suggestion.suggested_description,
                    is_billable=True
                )
                suggestion.generated_time_entry = time_entry
            
            elif action == 'modify':
                # Handle modifications
                if 'modified_start_time' in serializer.validated_data:
                    suggestion.suggested_start_time = serializer.validated_data['modified_start_time']
                if 'modified_end_time' in serializer.validated_data:
                    suggestion.suggested_end_time = serializer.validated_data['modified_end_time']
                if 'modified_description' in serializer.validated_data:
                    suggestion.suggested_description = serializer.validated_data['modified_description']
                
                suggestion.status = 'modified'
            
            suggestion.save()
            
            response_serializer = SmartTimesheetSuggestionSerializer(suggestion)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskAssignmentRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet for task assignment recommendations."""
    
    serializer_class = TaskAssignmentRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter recommendations based on user permissions."""
        user = self.request.user
        workspace_id = self.request.query_params.get('workspace')
        
        # Users can see recommendations for their projects or tasks
        queryset = TaskAssignmentRecommendation.objects.filter(
            Q(project__manager=user) |
            Q(project__members__user=user) |
            Q(recommended_assignee=user)
        ).distinct()
        
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_for_task(self, request):
        """Generate assignment recommendation for a task."""
        task_id = request.data.get('task_id')
        
        if not task_id:
            return Response(
                {'error': 'task_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not (task.project.manager == request.user or 
                task.project.members.filter(user=request.user).exists()):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate recommendation
        service = TaskAssignmentService()
        recommendation = service.recommend_assignee(task)
        
        if recommendation:
            serializer = TaskAssignmentRecommendationSerializer(recommendation)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Could not generate recommendation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a task assignment recommendation."""
        recommendation = self.get_object()
        
        if recommendation.status != 'pending':
            return Response(
                {'error': 'Only pending recommendations can be responded to'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskAssignmentActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            feedback = serializer.validated_data.get('feedback', '')
            
            recommendation.manager_feedback = feedback
            recommendation.responded_at = timezone.now()
            
            if action == 'accept':
                # Assign task to recommended user
                recommendation.task.assigned_to = recommendation.recommended_assignee
                recommendation.task.save()
                recommendation.status = 'accepted'
            
            elif action == 'reject':
                recommendation.status = 'rejected'
            
            elif action == 'select_alternative':
                # Assign task to alternative user
                alternative_user_id = serializer.validated_data['alternative_user_id']
                try:
                    from iam.models import User
                    alternative_user = User.objects.get(id=alternative_user_id)
                    recommendation.task.assigned_to = alternative_user
                    recommendation.task.save()
                    recommendation.status = 'accepted'
                except User.DoesNotExist:
                    return Response(
                        {'error': 'Alternative user not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            recommendation.save()
            
            response_serializer = TaskAssignmentRecommendationSerializer(recommendation)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIInsightViewSet(viewsets.ModelViewSet):
    """ViewSet for AI insights."""
    
    serializer_class = AIInsightSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter insights based on user permissions."""
        user = self.request.user
        workspace_id = self.request.query_params.get('workspace')
        insight_type = self.request.query_params.get('type')
        
        # Users can see workspace-wide insights and personal insights
        queryset = AIInsight.objects.filter(
            Q(workspace__memberships__user=user) |
            Q(user=user)
        ).distinct()
        
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_for_workspace(self, request):
        """Generate insights for a workspace."""
        workspace_id = request.data.get('workspace')
        
        if not workspace_id:
            return Response(
                {'error': 'workspace is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response(
                {'error': 'Workspace not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate insights
        service = AIInsightService()
        insights = service.generate_productivity_insights(workspace, request.user)
        
        serializer = AIInsightSerializer(insights, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an insight."""
        insight = self.get_object()
        
        serializer = InsightAcknowledgeSerializer(data=request.data)
        
        if serializer.is_valid():
            insight.is_acknowledged = True
            insight.acknowledged_by = request.user
            insight.acknowledged_at = timezone.now()
            insight.save()
            
            response_serializer = AIInsightSerializer(insight)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)