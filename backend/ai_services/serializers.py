from rest_framework import serializers
from django.utils import timezone
from .models import (
    AIModel, AIJob, SmartTimesheetSuggestion, 
    TaskAssignmentRecommendation, TaskAssignmentAlternative, AIInsight
)
from iam.models import User
from projects.models import Project
from tasks.models import Task


class AIModelSerializer(serializers.ModelSerializer):
    """Serializer for AI models."""
    
    class Meta:
        model = AIModel
        fields = [
            'id', 'name', 'model_type', 'version', 'status',
            'accuracy_score', 'precision_score', 'recall_score',
            'created_at', 'updated_at', 'last_trained_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIJobSerializer(serializers.ModelSerializer):
    """Serializer for AI processing jobs."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = AIJob
        fields = [
            'id', 'job_type', 'user', 'user_name', 'workspace', 'model', 'model_name',
            'priority', 'status', 'progress_percentage', 'error_message',
            'confidence_score', 'created_at', 'started_at', 'completed_at',
            'processing_time', 'input_data', 'output_data', 'result_metadata'
        ]
        read_only_fields = [
            'id', 'user_name', 'model_name', 'status', 'progress_percentage',
            'error_message', 'confidence_score', 'created_at', 'started_at',
            'completed_at', 'processing_time', 'output_data', 'result_metadata'
        ]


class SmartTimesheetSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for timesheet suggestions."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = SmartTimesheetSuggestion
        fields = [
            'id', 'user', 'user_name', 'workspace', 'suggestion_type', 'date',
            'project', 'project_name', 'task', 'task_title',
            'suggested_start_time', 'suggested_end_time', 'suggested_duration_minutes',
            'suggested_description', 'confidence_score', 'reasoning', 'source_data',
            'status', 'user_feedback', 'created_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'project_name', 'task_title', 'confidence_score',
            'reasoning', 'source_data', 'created_at', 'responded_at'
        ]


class TimesheetSuggestionActionSerializer(serializers.Serializer):
    """Serializer for timesheet suggestion actions."""
    
    action = serializers.ChoiceField(choices=['accept', 'reject', 'modify'])
    feedback = serializers.CharField(required=False, allow_blank=True)
    
    # For modify action
    modified_start_time = serializers.TimeField(required=False)
    modified_end_time = serializers.TimeField(required=False)
    modified_description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate action data."""
        action = data.get('action')
        
        if action == 'modify':
            if not any([
                data.get('modified_start_time'),
                data.get('modified_end_time'),
                data.get('modified_description')
            ]):
                raise serializers.ValidationError(
                    "At least one modification field is required when action is 'modify'"
                )
        
        return data


class TaskAssignmentRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for task assignment recommendations."""
    
    task_title = serializers.CharField(source='task.title', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    recommended_assignee_name = serializers.CharField(
        source='recommended_assignee.get_full_name', 
        read_only=True
    )
    alternatives = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskAssignmentRecommendation
        fields = [
            'id', 'task', 'task_title', 'project', 'project_name', 'workspace',
            'recommendation_type', 'recommended_assignee', 'recommended_assignee_name',
            'confidence_score', 'reasoning', 'analysis_data',
            'estimated_completion_time', 'predicted_quality_score', 'workload_impact',
            'status', 'manager_feedback', 'alternatives', 'created_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'task_title', 'project_name', 'recommended_assignee_name',
            'confidence_score', 'reasoning', 'analysis_data',
            'estimated_completion_time', 'predicted_quality_score', 'workload_impact',
            'alternatives', 'created_at', 'responded_at'
        ]
    
    def get_alternatives(self, obj):
        """Get alternative recommendations."""
        alternatives = obj.alternatives.all().order_by('ranking')
        return TaskAssignmentAlternativeSerializer(alternatives, many=True).data


class TaskAssignmentAlternativeSerializer(serializers.ModelSerializer):
    """Serializer for alternative task assignments."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TaskAssignmentAlternative
        fields = [
            'id', 'user', 'user_name', 'confidence_score', 
            'ranking', 'reasoning'
        ]
        read_only_fields = ['id', 'user_name']


class TaskAssignmentActionSerializer(serializers.Serializer):
    """Serializer for task assignment actions."""
    
    action = serializers.ChoiceField(choices=['accept', 'reject', 'select_alternative'])
    feedback = serializers.CharField(required=False, allow_blank=True)
    alternative_user_id = serializers.UUIDField(required=False)
    
    def validate(self, data):
        """Validate assignment action."""
        action = data.get('action')
        
        if action == 'select_alternative' and not data.get('alternative_user_id'):
            raise serializers.ValidationError(
                "alternative_user_id is required when selecting an alternative"
            )
        
        return data


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer for AI insights."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    acknowledged_by_name = serializers.CharField(
        source='acknowledged_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'insight_type', 'workspace', 'workspace_name', 'user', 'user_name',
            'project', 'project_name', 'title', 'description', 'severity',
            'insight_data', 'recommendations', 'confidence_score', 'valid_until',
            'is_acknowledged', 'acknowledged_by', 'acknowledged_by_name', 'acknowledged_at',
            'created_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'project_name', 'workspace_name', 'acknowledged_by_name',
            'confidence_score', 'created_at'
        ]


class InsightAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging insights."""
    
    acknowledge = serializers.BooleanField()
    
    def validate_acknowledge(self, value):
        """Validate acknowledge action."""
        if not value:
            raise serializers.ValidationError("acknowledge must be True to acknowledge an insight")
        return value


class AIJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AI jobs."""
    
    class Meta:
        model = AIJob
        fields = ['job_type', 'workspace', 'priority', 'input_data']
    
    def create(self, validated_data):
        """Create AI job with user and model assignment."""
        # Get appropriate model for job type
        job_type = validated_data['job_type']
        model = AIModel.objects.filter(
            model_type=job_type,
            status='active'
        ).first()
        
        if not model:
            raise serializers.ValidationError(f"No active model found for {job_type}")
        
        validated_data['model'] = model
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)