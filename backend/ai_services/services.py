import logging
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Q, Avg, Sum, Count
from django.contrib.auth import get_user_model

from .models import (
    AIModel, AIJob, SmartTimesheetSuggestion, 
    TaskAssignmentRecommendation, TaskAssignmentAlternative, AIInsight
)
from time_entries.models import TimeEntry
from projects.models import Project, ProjectMember
from tasks.models import Task
from organizations.models import Workspace

User = get_user_model()
logger = logging.getLogger(__name__)


class SmartTimesheetService:
    """AI service for generating intelligent timesheet suggestions."""
    
    def __init__(self):
        self.model = self._get_active_model('timesheet_generation')
    
    def _get_active_model(self, model_type: str) -> Optional[AIModel]:
        """Get active AI model for the given type."""
        try:
            return AIModel.objects.filter(
                model_type=model_type,
                status='active'
            ).first()
        except AIModel.DoesNotExist:
            logger.warning(f"No active AI model found for {model_type}")
            return None
    
    def generate_suggestions_for_user(
        self, 
        user: User, 
        workspace: Workspace, 
        date: datetime.date
    ) -> List[SmartTimesheetSuggestion]:
        """Generate timesheet suggestions for a user on a specific date."""
        suggestions = []
        
        # Pattern-based suggestions
        pattern_suggestions = self._generate_pattern_based_suggestions(user, workspace, date)
        suggestions.extend(pattern_suggestions)
        
        # Project deadline-based suggestions
        deadline_suggestions = self._generate_deadline_based_suggestions(user, workspace, date)
        suggestions.extend(deadline_suggestions)
        
        # Save suggestions to database
        saved_suggestions = []
        for suggestion_data in suggestions:
            suggestion = SmartTimesheetSuggestion.objects.create(**suggestion_data)
            saved_suggestions.append(suggestion)
        
        return saved_suggestions
    
    def _generate_pattern_based_suggestions(
        self, 
        user: User, 
        workspace: Workspace, 
        date: datetime.date
    ) -> List[Dict]:
        """Generate suggestions based on historical time entry patterns."""
        suggestions = []
        
        # Get historical data for the same day of week
        weekday = date.weekday()
        lookback_weeks = 8
        start_date = date - timedelta(weeks=lookback_weeks)
        
        # Get time entries for same weekday in past weeks
        historical_entries = TimeEntry.objects.filter(
            user=user,
            workspace=workspace,
            start_time__date__gte=start_date,
            start_time__date__lt=date,
            start_time__week_day=weekday + 1
        ).select_related('project', 'task')
        
        # Group by project and analyze patterns
        project_patterns = {}
        for entry in historical_entries:
            project_id = entry.project.id
            if project_id not in project_patterns:
                project_patterns[project_id] = {
                    'project': entry.project,
                    'entries': [],
                    'total_minutes': 0
                }
            
            project_patterns[project_id]['entries'].append(entry)
            project_patterns[project_id]['total_minutes'] += entry.duration_minutes or 0
        
        # Generate suggestions from patterns
        for project_id, pattern in project_patterns.items():
            if len(pattern['entries']) < 2:
                continue
            
            avg_duration = pattern['total_minutes'] / len(pattern['entries'])
            
            # Calculate most common start time
            start_times = [entry.start_time.time() for entry in pattern['entries']]
            avg_start_hour = sum(t.hour for t in start_times) / len(start_times)
            
            suggested_start = time(int(avg_start_hour), 0)
            suggested_end = (
                datetime.combine(date, suggested_start) + 
                timedelta(minutes=avg_duration)
            ).time()
            
            confidence = min(len(pattern['entries']) / 4.0, 0.9)
            
            if confidence >= 0.5:
                suggestions.append({
                    'user': user,
                    'workspace': workspace,
                    'suggestion_type': 'pattern_based',
                    'date': date,
                    'project': pattern['project'],
                    'task': None,
                    'suggested_start_time': suggested_start,
                    'suggested_end_time': suggested_end,
                    'suggested_duration_minutes': int(avg_duration),
                    'suggested_description': f"Work on {pattern['project'].name} (based on usual pattern)",
                    'confidence_score': Decimal(str(round(confidence, 4))),
                    'reasoning': f"Based on {len(pattern['entries'])} similar entries in the past {lookback_weeks} weeks",
                    'source_data': {
                        'historical_entries': len(pattern['entries']),
                        'avg_duration_minutes': avg_duration
                    }
                })
        
        return suggestions
    
    def _generate_deadline_based_suggestions(
        self, 
        user: User, 
        workspace: Workspace, 
        date: datetime.date
    ) -> List[Dict]:
        """Generate suggestions based on upcoming project deadlines."""
        suggestions = []
        
        # Get user's active projects with upcoming deadlines
        user_projects = Project.objects.filter(
            Q(members__user=user) | Q(manager=user),
            workspace=workspace,
            status='active',
            end_date__gte=date,
            end_date__lte=date + timedelta(days=14)
        ).distinct()
        
        for project in user_projects:
            days_until_deadline = (project.end_date - date).days
            urgency_score = max(0, (14 - days_until_deadline) / 14.0)
            
            estimated_duration = 120  # 2 hours default
            suggested_start = time(9, 0)
            suggested_end = (
                datetime.combine(date, suggested_start) + 
                timedelta(minutes=estimated_duration)
            ).time()
            
            confidence = 0.7 + (urgency_score * 0.3)
            
            suggestions.append({
                'user': user,
                'workspace': workspace,
                'suggestion_type': 'project_deadline',
                'date': date,
                'project': project,
                'task': None,
                'suggested_start_time': suggested_start,
                'suggested_end_time': suggested_end,
                'suggested_duration_minutes': estimated_duration,
                'suggested_description': f"Work on {project.name} (deadline: {project.end_date})",
                'confidence_score': Decimal(str(round(confidence, 4))),
                'reasoning': f"Project deadline in {days_until_deadline} days",
                'source_data': {
                    'days_until_deadline': days_until_deadline,
                    'urgency_score': urgency_score
                }
            })
        
        return suggestions


class TaskAssignmentService:
    """AI service for intelligent task assignment recommendations."""
    
    def __init__(self):
        self.model = self._get_active_model('task_assignment')
    
    def _get_active_model(self, model_type: str) -> Optional[AIModel]:
        """Get active AI model for the given type."""
        try:
            return AIModel.objects.filter(
                model_type=model_type,
                status='active'
            ).first()
        except AIModel.DoesNotExist:
            logger.warning(f"No active AI model found for {model_type}")
            return None
    
    def recommend_assignee(self, task: Task) -> Optional[TaskAssignmentRecommendation]:
        """Generate task assignment recommendation for a given task."""
        project = task.project
        workspace = project.workspace
        
        # Get all project members who could be assigned
        potential_assignees = User.objects.filter(
            project_memberships__project=project,
            project_memberships__is_active=True
        ).distinct()
        
        if not potential_assignees.exists():
            logger.warning(f"No potential assignees found for task {task.id}")
            return None
        
        # Analyze each potential assignee
        assignee_scores = []
        for user in potential_assignees:
            score_data = self._analyze_assignee_fit(task, user, workspace)
            assignee_scores.append((user, score_data))
        
        # Sort by overall score
        assignee_scores.sort(key=lambda x: x[1]['overall_score'], reverse=True)
        
        if not assignee_scores:
            return None
        
        # Create recommendation for best candidate
        best_assignee, best_score_data = assignee_scores[0]
        
        recommendation = TaskAssignmentRecommendation.objects.create(
            task=task,
            project=project,
            workspace=workspace,
            recommendation_type='workload_balancing',
            recommended_assignee=best_assignee,
            confidence_score=Decimal(str(round(best_score_data['overall_score'], 4))),
            reasoning=best_score_data['reasoning'],
            analysis_data=best_score_data,
            workload_impact='medium'
        )
        
        return recommendation
    
    def _analyze_assignee_fit(self, task: Task, user: User, workspace: Workspace) -> Dict:
        """Analyze how well a user fits for a specific task assignment."""
        # Simple workload analysis
        current_week_hours = TimeEntry.objects.filter(
            user=user,
            workspace=workspace,
            start_time__date__gte=timezone.now().date() - timedelta(days=7)
        ).aggregate(total=Sum('duration_minutes'))['total'] or 0
        
        current_week_hours = current_week_hours / 60.0
        workload_score = max(0, 1.0 - (current_week_hours / 40.0))
        
        # Performance based on completed tasks
        completed_tasks = Task.objects.filter(
            assigned_to=user,
            project=task.project,
            status='completed'
        ).count()
        
        performance_score = min(completed_tasks / 10.0, 1.0)
        
        # Overall score
        overall_score = (workload_score * 0.6) + (performance_score * 0.4)
        
        reasoning = f"Good workload balance ({current_week_hours:.1f}h this week)"
        if completed_tasks > 0:
            reasoning += f", {completed_tasks} tasks completed in this project"
        
        return {
            'overall_score': overall_score,
            'workload_score': workload_score,
            'performance_score': performance_score,
            'reasoning': reasoning,
            'current_week_hours': current_week_hours,
            'completed_tasks': completed_tasks
        }


class AIInsightService:
    """Service for generating AI-powered insights and analytics."""
    
    def generate_productivity_insights(
        self, 
        workspace: Workspace, 
        user: Optional[User] = None
    ) -> List[AIInsight]:
        """Generate productivity insights for workspace or specific user."""
        insights = []
        
        # Get recent data for analysis
        recent_hours = TimeEntry.objects.filter(
            workspace=workspace,
            start_time__gte=timezone.now() - timedelta(days=7)
        )
        
        if user:
            recent_hours = recent_hours.filter(user=user)
        
        total_hours = recent_hours.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        total_hours = total_hours / 60.0
        
        # Simple burnout detection
        if user and total_hours > 50:
            insight = AIInsight.objects.create(
                insight_type='burnout_prediction',
                workspace=workspace,
                user=user,
                title='High workload detected',
                description=f'User worked {total_hours:.1f} hours this week, which is above recommended levels.',
                severity='high' if total_hours > 60 else 'medium',
                insight_data={'weekly_hours': total_hours},
                recommendations=['Schedule time off', 'Review task priorities'],
                confidence_score=Decimal('0.8')
            )
            insights.append(insight)
        
        return insights